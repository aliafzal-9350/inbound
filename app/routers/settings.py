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
    "openai": "OpenAI",
    "gemini": "Google Gemini",
    "groq": "Groq (Llama-3.3)",
    "xai": "xAI (Grok)",
}

_PROVIDER_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "xai": "grok-3-mini",
}


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
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    key = groq_key or gemini_key or openai_key
    if not key:
        return {"configured": False, "masked_key": "", "provider": "none"}
    if groq_key or key.startswith("gsk_"):
        provider = "Groq Llama-3.3 (100% Free)"
    elif key.startswith("sk-"):
        provider = "OpenAI"
    else:
        provider = "Google Gemini (100% Free)"
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else "****"
    return {"configured": True, "masked_key": masked, "provider": provider}


@router.post("/api-key")
def update_api_key(payload: ApiKeyUpdate, tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    new_key = payload.openai_api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")

    if new_key.startswith("gsk_"):
        provider = "Groq Llama-3.3 (100% Free)"
        key_name = "GROQ_API_KEY"
    elif new_key.startswith("sk-"):
        provider = "OpenAI"
        key_name = "OPENAI_API_KEY"
    else:
        provider = "Google Gemini (100% Free)"
        key_name = "GEMINI_API_KEY"

    os.environ[key_name] = new_key
    _write_env_key(key_name, new_key)

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
    result = {}
    for provider_id, env_var in _PROVIDER_ENV_MAP.items():
        raw = (os.getenv(env_var) or "").strip()
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
    os.environ[env_var] = new_key
    _write_env_key(env_var, new_key)

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
    os.environ.pop(env_var, None)
    _write_env_key(env_var, None)  # removes the line from .env

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
    from ..services.llm_engine import LLMEngine
    from ..services.rag_engine import HybridRAGEngine
    from ..services.intent_router import is_pure_greeting, generate_instant_greeting_reply
    from ..services.ravisn_knowledge_base import RAVISNKnowledgeEngine, BookingDialogManager

    custom_prompt = payload.system_prompt.strip()
    msg = payload.message.strip()
    tenant_name = tenant.business_name or getattr(tenant, "name", None) or "RAVISN"

    import re
    lang = "urdu_nastaliq" if re.search(r"[\u0600-\u06FF]", msg) else ("roman_urdu" if any(k in msg.lower() for k in ["salam", "assalam", "asslamualikom", "aoa", "kya", "hai", "kese", "kaise", "chahiye", "karwana"]) else "english")

    # 1. Instant sub-5ms fast path for greetings
    if is_pure_greeting(msg):
        fast_reply = generate_instant_greeting_reply(msg, tenant_name)
        return {
            "reply": fast_reply,
            "assistant_reply": fast_reply,
            "language": lang,
            "intent": "greeting",
            "booking_ready": False,
            "booking_info": {"name": None, "contact": None, "preferred_time": None, "service": None},
            "evidence_used": False
        }



    # 3. Interactive Multi-Step Demo / Consultation Booking Flow
    if BookingDialogManager.detect_booking_intent(msg):
        reply_text, next_step, updated_slots, is_complete = BookingDialogManager.process_turn(
            user_message=msg,
            current_step="idle",
            booking_data={},
            language=lang,
            db_session=db,
            tenant_id=tenant.id
        )
        return {
            "reply": reply_text,
            "assistant_reply": reply_text,
            "language": lang,
            "intent": "booking_request",
            "booking_ready": is_complete,
            "booking_info": {
                "name": updated_slots.get("name"),
                "contact": updated_slots.get("email") or "+1 (564) 222-6889",
                "preferred_time": updated_slots.get("preferred_time"),
                "service": updated_slots.get("service_needed") or "AI Automation Consultation"
            },
            "evidence_used": True
        }

    # 4. Dynamic Hybrid RAG + Local LLM Generation
    chunks = HybridRAGEngine.search(db, tenant.id, msg, top_k=3)
    evidence_pack = HybridRAGEngine.build_evidence_pack(chunks)

    inf_output = await LLMEngine.generate_single_pass_inference(
        tenant_name=tenant_name,
        timezone=getattr(tenant, "default_timezone", None) or getattr(tenant, "timezone", None) or "Asia/Karachi",
        fsm_state="SIMULATION",
        collected_slots={},
        available_slots=[],
        evidence_pack=evidence_pack,
        conversation_history=[],
        user_message=msg,
        system_prompt_override=custom_prompt
    )

    slots = inf_output.extracted_slots
    is_booking = inf_output.detected_intent in ("booking", "booking_request") or bool(slots.customer_name or slots.preferred_time)

    return {
        "reply": inf_output.assistant_reply,
        "assistant_reply": inf_output.assistant_reply,
        "language": inf_output.detected_language,
        "intent": inf_output.detected_intent,
        "booking_ready": is_booking,
        "booking_info": {
            "name": slots.customer_name,
            "contact": slots.customer_phone or slots.customer_email,
            "preferred_time": f"{slots.preferred_date or ''} {slots.preferred_time or ''}".strip() or None,
            "service": slots.service_name
        },
        "evidence_used": bool(evidence_pack)
    }


