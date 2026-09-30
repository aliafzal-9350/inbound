"""The agent's AI brain: Groq only (https://console.groq.com).

Each tier walks a list of Groq models: Groq rate limits are per model, so a model that is
rate-limited (429) or overloaded is parked briefly and the next one answers. The API key is read
at call time (core.api_keys), so a key rotated from the dashboard takes effect without a restart.
"""
import asyncio
import json
import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional

import httpx

from ..core.api_keys import get_key
from ..core.config import settings

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMUnavailable(Exception):
    """No Groq model produced a usable answer for this call."""


_parked_until: Dict[str, float] = {}


def _park(key: str, seconds: float) -> None:
    _parked_until[key] = time.time() + seconds


def _parked(key: str) -> bool:
    return _parked_until.get(key, 0) > time.time()


_http_clients: Dict[int, httpx.AsyncClient] = {}


def _http() -> httpx.AsyncClient:
    """One pooled client per event loop (reuses TLS connections; pools can't cross loops, and the
    sync endpoints - dashboard test chat, WhatsApp QR webhook - run each message in a fresh loop)."""
    loop_id = id(asyncio.get_running_loop())
    client = _http_clients.get(loop_id)
    if client is None:
        if len(_http_clients) >= 16:
            _http_clients.pop(next(iter(_http_clients)))
        client = _http_clients[loop_id] = httpx.AsyncClient(timeout=20.0)
    return client


def _models(tier: str) -> List[str]:
    if tier == "fast":
        primary, fallbacks = settings.GROQ_FAST_MODEL, settings.GROQ_FAST_FALLBACKS
    else:
        primary, fallbacks = settings.GROQ_MODEL, settings.GROQ_SMART_FALLBACKS
    models: List[str] = []
    for m in [primary] + (fallbacks or "").split(","):
        m = m.strip()
        if m and m not in models:
            models.append(m)
    return models


def _model_options(model: str) -> Dict[str, Any]:
    if model.startswith("openai/gpt-oss"):
        return {"reasoning_effort": "low"}       # reasoning models: keep latency ~1s
    if model.startswith("qwen/"):
        return {"reasoning_format": "hidden"}     # never leak <think> blocks into replies
    return {}


def parse_json(raw: str) -> Dict[str, Any]:
    """Parses model JSON output, tolerating code fences and leading/trailing prose."""
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value


async def _call_groq(key: str, model: str, system: str, prompt: str, json_mode: bool,
                     temperature: float, timeout: float) -> str:
    body: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "temperature": temperature,
        **_model_options(model),
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    resp = await _http().post(GROQ_CHAT_URL, json=body, timeout=timeout,
                              headers={"Authorization": f"Bearer {key}"})
    if resp.status_code == 429:
        retry = resp.headers.get("retry-after")
        _park(f"groq:{model}", min(float(retry), 120.0) if retry and retry.replace(".", "").isdigit() else 30.0)
    elif resp.status_code == 404:
        _park(f"groq:{model}", 6 * 3600)          # model retired / not on this account
    elif resp.status_code in (401, 403):
        _park("groq:key", 30)                      # bad key: re-check soon (it may be rotated from the dashboard)
    resp.raise_for_status()
    text = (resp.json()["choices"][0]["message"].get("content") or "").strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    if not text:
        raise ValueError("empty response")
    return text


async def generate(system: str, prompt: str, *, tier: str = "smart", json_mode: bool = False,
                   temperature: float = 0.3, timeout: float = 12.0,
                   validate: Optional[Callable[[str], bool]] = None) -> str:
    """Returns the model's text. `validate` can reject an answer (e.g. wrong script) so the next model
    tries. Raises LLMUnavailable if no model produced an acceptable answer."""
    key = get_key("GROQ_API_KEY")
    if not key:
        raise LLMUnavailable("GROQ_API_KEY is not set")
    if _parked("groq:key"):
        raise LLMUnavailable("Groq rejected the API key (401) - update it in Settings > API keys")

    errors: List[str] = []
    deadline = time.time() + timeout
    per_attempt = 5.0 if tier == "fast" else 8.0
    for model in _models(tier):
        if _parked(f"groq:{model}"):
            continue
        remaining = deadline - time.time()
        if remaining < 1.0:
            break
        try:
            text = await _call_groq(key, model, system, prompt, json_mode, temperature, min(remaining, per_attempt))
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            errors.append(f"{model}: {status or type(e).__name__} {str(e)[:120]}")
            if status in (401, 403):
                break
            continue
        if validate and not validate(text):
            errors.append(f"{model}: reply rejected by validator")
            continue
        return text

    logger.error("[LLM] Groq failed: %s", " | ".join(errors) or "all models rate-limited")
    raise LLMUnavailable("; ".join(errors) or "all Groq models are rate-limited")


async def generate_json(system: str, prompt: str, *, tier: str = "fast",
                        temperature: float = 0.1, timeout: float = 10.0) -> Dict[str, Any]:
    """Like generate() but returns a parsed JSON object (models that return malformed JSON are skipped)."""
    parsed: Dict[str, Any] = {}

    def valid_json(text: str) -> bool:
        try:
            parsed["value"] = parse_json(text)
            return True
        except (ValueError, json.JSONDecodeError):
            return False

    await generate(system, prompt, tier=tier, json_mode=True, temperature=temperature, timeout=timeout,
                   validate=valid_json)
    return parsed["value"]
