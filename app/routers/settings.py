import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from .. import models, crud, agent
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/settings", tags=["settings"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROVIDER_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
}

_PROVIDER_LABELS = {
    "openai": "OpenAI (not used)",
    "gemini": "Google Gemini (knowledge search only)",
    "groq": "Groq (main AI brain)",
    "xai": "xAI Grok (not used)",
}

_PROVIDER_MODELS = {
    "openai": "-",
    "gemini": "gemini-embedding-001",
    "groq": "qwen/qwen3.8-27b + openai/gpt-oss-120b",
    "xai": "-",
}


def _verify_groq_key(key: str) -> None:
    """Rejects a Groq key that Groq itself refuses, so a typo can't take the agent offline."""
    import httpx
    try:
        resp = httpx.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {key}"}, timeout=15)
    except Exception:
        return  # Groq unreachable right now: accept the key rather than block the update
    if resp.status_code in (401, 403):
        raise HTTPException(status_code=400, detail="Groq rejected this API key. Please check it and try again.")


def _save_key(env_var: str, value: Optional[str]) -> None:
    """Applies a key to all workers now (Redis) and to .env for the next restart."""
    from ..core.api_keys import set_key
    if env_var == "GROQ_API_KEY" and value:
        _verify_groq_key(value)
    set_key(env_var, value)
    _write_env_key(env_var, value)


def _mask(key: str) -> str:
    if not key:
        return ""
    return key[:7] + "..." + key[-4:] if len(key) > 11 else "****"


def _write_env_key(key_name: str, value: Optional[str]) -> None:
    """Write or remove a key in the root .env file."""
    try:
        env_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        )
        lines: list[str] = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated = False
        new_lines: list[str] = []
        for line in lines:
            if line.strip().startswith(f"{key_name}="):
                if value is not None:
                    new_lines.append(f"{key_name}={value}\n")
                    updated = True
                # if value is None → skip line (delete it)
            else:
                new_lines.append(line)

        if value is not None and not updated:
            new_lines.append(f"\n{key_name}={value}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Legacy single-key endpoint (kept for backward compatibility)
# ---------------------------------------------------------------------------

class ApiKeyUpdate(BaseModel):
    openai_api_key: str


@router.get("/api-key")
def get_api_key(tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    from ..core.api_keys import get_key
    key = get_key("GROQ_API_KEY") or ""
    if not key:
        return {"configured": False, "masked_key": "", "provider": "none"}
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else "****"
    return {"configured": True, "masked_key": masked, "provider": _PROVIDER_LABELS["groq"]}


@router.post("/api-key")
def update_api_key(payload: ApiKeyUpdate, tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    new_key = payload.openai_api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")

    if new_key.startswith("gsk_"):
        provider, key_name = _PROVIDER_LABELS["groq"], "GROQ_API_KEY"
    elif new_key.startswith("sk-"):
        provider, key_name = _PROVIDER_LABELS["openai"], "OPENAI_API_KEY"
    else:
        provider, key_name = _PROVIDER_LABELS["gemini"], "GEMINI_API_KEY"

    _save_key(key_name, new_key)

    masked = _mask(new_key)
    return {
        "status": "ok",
        "message": f"{provider} API Key saved and active for real-time replies!",
        "configured": True,
        "masked_key": masked,
        "provider": provider,
    }


# ---------------------------------------------------------------------------
# New per-provider endpoints
# ---------------------------------------------------------------------------

@router.get("/api-keys")
def get_all_api_keys(tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    """Return masked status for all four AI providers."""
    from ..core.api_keys import get_key
    result = {}
    for provider_id, env_var in _PROVIDER_ENV_MAP.items():
        raw = get_key(env_var) or ""
        result[provider_id] = {
            "provider": provider_id,
            "label": _PROVIDER_LABELS[provider_id],
            "model": _PROVIDER_MODELS[provider_id],
            "env_var": env_var,
            "configured": bool(raw),
            "masked_key": _mask(raw) if raw else "",
        }
    return result


class ProviderKeyUpdate(BaseModel):
    api_key: str


@router.post("/api-keys/{provider}")
def save_provider_key(
    provider: str,
    payload: ProviderKeyUpdate,
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    """Save / update an API key for a specific provider."""
    if provider not in _PROVIDER_ENV_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'. Valid: openai, gemini, groq, xai")

    new_key = payload.api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    env_var = _PROVIDER_ENV_MAP[provider]
    _save_key(env_var, new_key)

    return {
        "status": "ok",
        "provider": provider,
        "label": _PROVIDER_LABELS[provider],
        "configured": True,
        "masked_key": _mask(new_key),
        "message": f"{_PROVIDER_LABELS[provider]} API key saved successfully!",
    }


@router.delete("/api-keys/{provider}")
def delete_provider_key(
    provider: str,
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    """Remove an API key for a specific provider (blanks it out from .env and memory)."""
    if provider not in _PROVIDER_ENV_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'. Valid: openai, gemini, groq, xai")

    env_var = _PROVIDER_ENV_MAP[provider]
    _save_key(env_var, None)  # removes it from Redis and .env

    return {
        "status": "ok",
        "provider": provider,
        "label": _PROVIDER_LABELS[provider],
        "configured": False,
        "masked_key": "",
        "message": f"{_PROVIDER_LABELS[provider]} API key removed.",
    }


class SystemPromptUpdate(BaseModel):
    system_prompt: str


class SystemPromptTestIn(BaseModel):
    system_prompt: str
    message: str


DEFAULT_PROMPT_TEMPLATES = [
    {
        "id": "professional_support",
        "name": "👔 Professional Support",
        "description": "Polite, formal, and authoritative. Ideal for corporate, B2B, and professional services.",
        "prompt": "You are a professional, polite, and helpful AI support representative for {tenant_name}.\n\nRules:\n1. Maintain a professional, empathetic, and respectful tone at all times.\n2. Answer customer queries strictly using the provided knowledge base.\n3. If a question is outside the knowledge base, politely state that our team will follow up shortly.\n4. If the customer wishes to book an appointment, collect their name, contact detail, and preferred time gracefully."
    },
    {
        "id": "friendly_sales",
        "name": "🚀 Friendly Sales & Appointment Setter",
        "description": "Energetic, engaging, and focused on turning conversations into bookings.",
        "prompt": "You are a friendly, enthusiastic, and high-converting sales assistant for {tenant_name}.\n\nRules:\n1. Be warm, welcoming, and use conversational language suitable for chat apps.\n2. Highlight key benefits of our services based on the knowledge base.\n3. Actively encourage customers to book a consultation or appointment when they express interest.\n4. Collect their name, contact details, and preferred appointment time."
    },
    {
        "id": "medical_clinic",
        "name": "🏥 Medical & Clinic Assistant",
        "description": "Warm, empathetic, and disclaimer-ready for healthcare and clinical services.",
        "prompt": "You are a caring and attentive clinic coordinator for {tenant_name}.\n\nRules:\n1. Be compassionate and gentle in your communication.\n2. Answer clinic timings, doctor schedules, and service details strictly from the knowledge base.\n3. For medical emergencies, advise the patient to visit the nearest hospital or emergency room immediately.\n4. Assist patients in booking appointments by collecting name, phone number, and preferred date/time."
    },
    {
        "id": "ecommerce_retail",
        "name": "🛒 E-Commerce & Service Assistant",
        "description": "Concise, direct, and focused on quick answers about products, pricing, and orders.",
        "prompt": "You are a fast, helpful customer service assistant for {tenant_name}.\n\nRules:\n1. Give short, direct, and crystal-clear answers.\n2. Provide accurate pricing, product info, and policy details from the knowledge base.\n3. Offer quick guidance on how to order or get in touch with our team."
    }
]


@router.get("/system-prompt")
def get_system_prompt(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    saved_prompt = crud.get_tenant_system_prompt(db, tenant.id)
    return {
        "system_prompt": saved_prompt,
        "default_templates": DEFAULT_PROMPT_TEMPLATES
    }


@router.post("/system-prompt")
def update_system_prompt(
    payload: SystemPromptUpdate,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    updated = crud.update_tenant_system_prompt(db, tenant.id, payload.system_prompt.strip())
    return {
        "status": "ok",
        "message": "Custom System Prompt saved and active for your AI agent!",
        "system_prompt": updated
    }


@router.post("/system-prompt/test")
async def test_system_prompt(
    payload: SystemPromptTestIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    """Runs one message through the real sales agent with the (unsaved) prompt. Dry run: the
    conversation is never saved and no booking or staff alert is triggered."""
    from types import SimpleNamespace
    from ..services import sales_agent

    trial_tenant = SimpleNamespace(
        id=tenant.id, business_name=tenant.business_name, name=getattr(tenant, "name", None),
        default_timezone=getattr(tenant, "default_timezone", None),
        system_prompt_override=payload.system_prompt.strip() or None, custom_system_prompt=None,
    )
    convo = models.Conversation(tenant_id=tenant.id, channel="web", contact_external_id="system-prompt-test")
    turn = await sales_agent.handle_turn(db, trial_tenant, convo, "web", payload.message.strip(), [], dry_run=True)
    lead = (convo.agent_state or {}).get("lead", {})
    return {
        "reply": turn.reply,
        "assistant_reply": turn.reply,
        "language": turn.language,
        "intent": ",".join(turn.intents),
        "booking_ready": False,
        "booking_info": {
            "name": lead.get("name"),
            "contact": lead.get("email") or lead.get("phone"),
            "preferred_time": lead.get("meeting_time"),
            "service": lead.get("goal"),
        },
        "evidence_used": not turn.degraded,
    }


