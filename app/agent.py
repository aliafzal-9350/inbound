import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from . import models
from .services.rag_engine import HybridRAGEngine
from .services.llm_engine import LLMEngine, LinguisticNormalizer
from .services.intent_router import is_pure_greeting
from .schemas.inference import AgentInferenceOutput


def generate_reply(
    tenant_name: str,
    kb_entries: List[models.KnowledgeEntry],
    history: List[models.Message],
    new_message: str,
    custom_prompt: str = ""
) -> Dict[str, Any]:
    """Backward-compatible agent function delegating to the unified single-pass LLM reasoning engine."""
    # Convert history
    history_formatted = [
        {"role": "user" if m.direction == "inbound" else "assistant", "content": m.body}
        for m in history
    ]

    # Convert kb_entries to text evidence pack (Zero-RAG Bypass if pure greeting)
    if is_pure_greeting(new_message):
        evidence_pack = ""
    else:
        chunks = []
        for e in kb_entries:
            chunks.append({
                "category": "FAQ",
                "title": e.question,
                "content": f"Q: {e.question}\nA: {e.answer}"
            })
        evidence_pack = HybridRAGEngine.build_evidence_pack(chunks)


    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run,
                    LLMEngine.generate_single_pass_inference(
                        tenant_name=tenant_name,
                        timezone="Asia/Karachi",
                        fsm_state="IDLE",
                        collected_slots={},
                        available_slots=["10:00 AM", "02:00 PM", "05:00 PM"],
                        evidence_pack=evidence_pack,
                        conversation_history=history_formatted,
                        user_message=new_message,
                        system_prompt_override=custom_prompt
                    )
                ).result()
        else:
            result = loop.run_until_complete(
                LLMEngine.generate_single_pass_inference(
                    tenant_name=tenant_name,
                    timezone="Asia/Karachi",
                    fsm_state="IDLE",
                    collected_slots={},
                    available_slots=["10:00 AM", "02:00 PM", "05:00 PM"],
                    evidence_pack=evidence_pack,
                    conversation_history=history_formatted,
                    user_message=new_message,
                    system_prompt_override=custom_prompt
                )
            )
    except Exception:
        result = LLMEngine._rule_based_fallback(
            new_message,
            LinguisticNormalizer.detect_script_mode(new_message),
            {},
            evidence_pack,
            LinguisticNormalizer.check_escalation_intent(new_message)
        )

    # Format return to match expected legacy keys
    extracted = result.extracted_slots
    is_ready = bool(extracted.customer_name and (extracted.customer_phone or extracted.preferred_time))
    
    return {
        "reply": result.assistant_reply,
        "detected_intent": result.detected_intent,
        "booking_ready": is_ready,
        "booking_info": {
            "name": extracted.customer_name or "Test User",
            "contact": extracted.customer_phone,
            "preferred_time": f"{extracted.preferred_date or ''} {extracted.preferred_time or ''}".strip() or "Tomorrow 5 PM",
            "resolved_datetime_iso": None,
            "notes": extracted.service_name or extracted.notes or "Consultation",
        },
        "escalate_to_human": result.requires_human_escalation,
    }
