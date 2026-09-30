"""Gemini text embeddings for knowledge search (the only thing Gemini is used for), normalized to unit
length so dot product == cosine similarity."""
import asyncio
import logging
import math
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from ..core.api_keys import get_key
from ..core.config import settings

logger = logging.getLogger(__name__)

_clients: Dict[Tuple[int, str], Any] = {}


def _gemini():
    """One client per (event loop, key): async connection pools can't be shared across loops, and the
    key can be rotated from the dashboard."""
    from google import genai
    key = get_key("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set (needed for knowledge-search embeddings)")
    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = 0
    client = _clients.get((loop_id, key))
    if client is None:
        if len(_clients) >= 16:
            _clients.pop(next(iter(_clients)))
        client = _clients[(loop_id, key)] = genai.Client(api_key=key)
    return client

_BATCH = 80  # each text counts toward the per-minute quota (100 on the free tier)
_query_cache: "OrderedDict[str, List[float]]" = OrderedDict()
_QUERY_CACHE_MAX = 1024


def _normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def model_signature() -> str:
    """Stored next to each vector so a model/dimension change triggers re-embedding."""
    return f"{settings.GEMINI_EMBED_MODEL}:{settings.EMBEDDING_DIM}"


def _retry_after(error: Exception) -> float:
    match = re.search(r"retry in ([\d.]+)s", str(error))
    return float(match.group(1)) + 1.0 if match else 30.0


async def embed_texts(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT",
                      timeout: float = 20.0, patient: bool = False) -> List[List[float]]:
    """Embeds texts in batches. task_type: RETRIEVAL_DOCUMENT for knowledge, RETRIEVAL_QUERY for searches.
    patient=True waits out rate limits (free tier: 100 texts/minute) - for background backfills only."""
    if not texts:
        return []
    from google.genai import types

    vectors: List[List[float]] = []
    for start in range(0, len(texts), _BATCH):
        batch = texts[start:start + _BATCH]
        for attempt in range(4 if patient else 1):
            try:
                response = await asyncio.wait_for(
                    _gemini().aio.models.embed_content(
                        model=settings.GEMINI_EMBED_MODEL,
                        contents=batch,
                        config=types.EmbedContentConfig(task_type=task_type,
                                                        output_dimensionality=settings.EMBEDDING_DIM),
                    ),
                    timeout=timeout,
                )
                break
            except Exception as e:
                if not patient or getattr(e, "code", None) != 429 or attempt == 3:
                    raise
                wait = min(_retry_after(e), 65.0)
                logger.info("[Embeddings] rate limited, waiting %.0fs", wait)
                await asyncio.sleep(wait)
        vectors.extend(_normalize(list(e.values)) for e in response.embeddings)
    return vectors


async def embed_queries(queries: List[str]) -> List[Optional[List[float]]]:
    """Embeds search queries with an LRU cache; returns None entries if embedding fails."""
    keys = [q.strip().lower() for q in queries]
    missing = [q for q, k in zip(queries, keys) if k not in _query_cache]
    if missing:
        try:
            for q, vec in zip(missing, await embed_texts(missing, task_type="RETRIEVAL_QUERY", timeout=5.0)):
                _query_cache[q.strip().lower()] = vec
                if len(_query_cache) > _QUERY_CACHE_MAX:
                    _query_cache.popitem(last=False)
        except Exception as e:
            logger.warning("[Embeddings] query embedding failed, falling back to keyword search: %s", e)
    return [_query_cache.get(k) for k in keys]
