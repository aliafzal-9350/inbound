import os
import re
import json
import logging
import datetime
from typing import Dict, Any, List, Optional
import httpx
from ..core.config import settings
from ..schemas.inference import AgentInferenceOutput, BookingSlotData

logger = logging.getLogger(__name__)

# Master Grounded Semantic RAG System Prompt Template
MASTER_SYSTEM_PROMPT = """You are a company knowledge assistant for {tenant_business_name}.
Current Date/Time: {current_datetime} ({tenant_timezone})

Your core purpose is to answer user inquiries naturally, accurately, and conversationally based STRICTLY on the retrieved company knowledge provided below.

### CRITICAL RULES FOR REASONING & GENERATION:
1. SEMANTIC UNDERSTANDING: Understand the user's intent semantically across variations, paraphrases, and colloquial wording (e.g. "developers", "engineering team", "technical team", "dev team", "software team").
2. GROUNDED SOURCE OF TRUTH: Use the [VERIFIED COMPANY KNOWLEDGE] as the sole source of truth for company facts.
3. NO EXACT MATCH REQUIREMENT: Do not require the user's wording to match the stored knowledge wording.
4. SYNTHESIZE NATURALLY: Rephrase, summarize, and synthesize information naturally. NEVER blindly copy or regurgitate stored answers word-for-word.
5. ZERO HALLUCINATION (STRICT): NEVER fabricate or invent facts, statistics, employee numbers, technologies, certifications, clients, locations, pricing, or services that are not explicitly present in the [VERIFIED COMPANY KNOWLEDGE].
6. PARTIAL KNOWLEDGE HANDLING: If the retrieved knowledge partially answers the inquiry, answer only the supported part, and clearly state what is not confirmed (for example: if the knowledge only says "We have multiple developer teams", and user asks "Do you have AI developers?", state that we have multiple developer teams, but available company knowledge does not confirm whether they are specifically focused on AI).
7. KNOWLEDGE LIMITATION / FALLBACK: If the retrieved knowledge contains NO relevant information or the question is completely out of scope / unrelated (e.g., weather, general trivia, unknown company facts), clearly and politely state: "{fallback_message}".
8. COMBINING SOURCES: If multiple knowledge items are provided, combine them into one coherent, unified response.
9. MULTI-TURN CONVERSATION MEMORY: Use [RECENT CONVERSATION HISTORY] to resolve pronouns ("they", "it", "them") and follow-up questions in context.
10. SCRIPT & LANGUAGE MIRRORING:
   - If user writes in Roman Urdu, reply in natural Roman Urdu.
   - If user writes in Urdu script, reply in Urdu script.
   - If user writes in English, reply in crisp English.
11. PRIVACY & CONVERSATIONAL STYLE: Never mention internal implementation details like "RAG", "vector search", "retrieved chunks", "database", or "knowledge chunks". Keep replies concise (under 70 words) and conversational.

[VERIFIED COMPANY KNOWLEDGE]
{retrieved_evidence_chunks}

[RECENT CONVERSATION HISTORY]
{conversation_history_text}

[CURRENT CONVERSATION STATE]
- State: {fsm_state}
- Collected Slots: {collected_slots_json}
- Available Calendar Slots: {available_calendar_slots}

### RESPONSE SCHEMA:
You MUST output a valid JSON object matching this schema:
{{
  "detected_language": "english" | "urdu_nastaliq" | "roman_urdu",
  "detected_intent": "greeting" | "inquiry" | "pricing" | "booking_request" | "reschedule" | "cancel" | "human_escalation" | "out_of_scope",
  "extracted_slots": {{
    "customer_name": null,
    "customer_phone": null,
    "customer_email": null,
    "service_name": null,
    "preferred_date": null,
    "preferred_time": null,
    "notes": null
  }},
  "requires_human_escalation": false,
  "escalation_reason": null,
  "confidence_score": 0.95,
  "assistant_reply": "string (concise, grounded natural answer)"
}}
"""


class LinguisticNormalizer:
    URDU_UNICODE_PATTERN = re.compile(r"[\u0600-\u06FF]")
    
    ROMAN_URDU_KEYWORDS = {
        "salam", "assalam", "asslamualikom", "assalamualaykum", "asalam", "aslam", "aoa", "walaikum", "bhai",
        "aap", "ap", "kya", "kia", "hai", "hain", "chahiye", "kitne", "kitna", "shukriya", "bohat", "boht",
        "mein", "main", "hoga", "hogi", "kab", "kal", "aaj", "parso", "subah", "sham", "dopahar", "raat",
        "baje", "krdo", "kardo", "karna", "krna", "chahye", "rate", "btao", "batao", "mil", "sakta",
        "sakty", "wali", "wala", "booking", "shubh", "naam", "rabta", "theek", "shukria", "sunayein",
        "sunaye", "kaisay", "kaise", "haal"
    }

    ESCALATION_KEYWORDS = {
        "connect me to human", "bande se baat krao", "bande se baat karao", "agent please",
        "human agent", "talk to human", "manager se baat", "scam", "ruined", "lawyer",
        "sue you", "fake", "bakwas", "rude staff", "refund my money", "cheater", "fraud"
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def detect_script_mode(cls, text: str) -> str:
        clean = cls.clean_text(text)
        if cls.URDU_UNICODE_PATTERN.search(clean):
            return "urdu_nastaliq"

        tokens = set(re.findall(r"\b[a-zA-Z]+\b", clean.lower()))
        if tokens and len(tokens.intersection(cls.ROMAN_URDU_KEYWORDS)) >= 1:
            return "roman_urdu"

        return "english"

    @classmethod
    def check_escalation_intent(cls, text: str) -> bool:
        clean = cls.clean_text(text).lower()
        return any(k in clean for k in cls.ESCALATION_KEYWORDS)





class LLMEngine:
    @classmethod
    async def generate_single_pass_inference(
        cls,
        tenant_name: str,
        timezone: str,
        fsm_state: str,
        collected_slots: Dict[str, Any],
        available_slots: List[str],
        evidence_pack: str,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        system_prompt_override: Optional[str] = None,
    ) -> AgentInferenceOutput:
        """Executes single-pass structured LLM reasoning and extraction with fast cloud Groq prioritized and local/cloud failovers."""
        cleaned_user_message = LinguisticNormalizer.clean_text(user_message)
        script_mode = LinguisticNormalizer.detect_script_mode(cleaned_user_message)
        has_escalation_phrase = LinguisticNormalizer.check_escalation_intent(cleaned_user_message)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fallback_msg = getattr(settings, "RAG_FALLBACK_MESSAGE", "I don't have enough information in the available company knowledge to answer that accurately.")

        # Build conversation history text
        history_lines = []
        if conversation_history:
            for turn in conversation_history[-8:]:
                role = "User" if turn.get("role") == "user" else "Assistant"
                history_lines.append(f"{role}: {turn.get('content', '')}")
        history_text = "\n".join(history_lines) if history_lines else "None (Beginning of conversation)"

        evidence_text = evidence_pack.strip() if evidence_pack and evidence_pack.strip() else "No matching company knowledge found."

        prompt = MASTER_SYSTEM_PROMPT.format(
            tenant_business_name=tenant_name or "Company",
            current_datetime=now_str,
            tenant_timezone=timezone or "Asia/Karachi",
            retrieved_evidence_chunks=evidence_text,
            conversation_history_text=history_text,
            fsm_state=fsm_state or "IDLE",
            collected_slots_json=json.dumps(collected_slots or {}),
            available_calendar_slots=", ".join(available_slots) if available_slots else "None currently specified",
            fallback_message=fallback_msg
        )

        if system_prompt_override:
            prompt += f"\n[TENANT CUSTOM INSTRUCTIONS]\n{system_prompt_override}"

        if getattr(settings, "RAG_DEBUG_LOGGING", True):
            logger.info(f"[LLM PIPELINE] Query: '{cleaned_user_message}' | Evidence Chunks Present: {bool(evidence_pack)}")

        # 1. Try Groq Cloud (Ultra-fast ~300ms)
        if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_placeholder"):
            try:
                res = await cls._call_groq(prompt, conversation_history, cleaned_user_message)
                if res:
                    if has_escalation_phrase:
                        res.requires_human_escalation = True
                    if getattr(settings, "RAG_DEBUG_LOGGING", True):
                        logger.info(f"[LLM SUCCESS via Groq] Reply: '{res.assistant_reply}'")
                    return res
            except Exception as e:
                logger.warning(f"Groq LLM call failed, trying Gemini: {e}")

        # 2. Try Google Gemini
        if settings.GEMINI_API_KEY:
            try:
                res = await cls._call_gemini(prompt, conversation_history, cleaned_user_message)
                if res:
                    if has_escalation_phrase:
                        res.requires_human_escalation = True
                    return res
            except Exception as e:
                logger.warning(f"Gemini LLM call failed, trying OpenAI: {e}")

        # 4. Try xAI (Grok)
        if settings.XAI_API_KEY:
            try:
                res = await cls._call_xai(prompt, conversation_history, cleaned_user_message)
                if res:
                    if has_escalation_phrase:
                        res.requires_human_escalation = True
                    if getattr(settings, "RAG_DEBUG_LOGGING", True):
                        logger.info(f"[LLM SUCCESS via xAI Grok] Reply: '{res.assistant_reply}'")
                    return res
            except Exception as e:
                logger.warning(f"xAI LLM call failed, trying OpenAI: {e}")

        # 5. Try OpenAI
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("placeholder"):
            try:
                res = await cls._call_openai(prompt, conversation_history, cleaned_user_message)
                if res:
                    if has_escalation_phrase:
                        res.requires_human_escalation = True
                    return res
            except Exception as e:
                logger.warning(f"OpenAI LLM call failed: {e}")

        # 6. Grounded Knowledge Fallback
        if getattr(settings, "RAG_DEBUG_LOGGING", True):
            logger.info(f"[LLM FALLBACK TRIGGERED] Returning grounded fallback response.")
        return cls._rule_based_fallback(
            cleaned_user_message, script_mode, collected_slots, evidence_pack, has_escalation_phrase
        )

    @classmethod
    def _build_openai_messages(cls, system_prompt: str, history: List[Dict[str, str]], message: str) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-8:]:
            role = "assistant" if h.get("role") in ("assistant", "model") else "user"
            messages.append({"role": role, "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})
        return messages

    @classmethod
    async def _call_groq(
        cls,
        system_prompt: str,
        history: List[Dict[str, str]],
        message: str
    ) -> Optional[AgentInferenceOutput]:
        messages = cls._build_openai_messages(system_prompt, history, message)

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            resp.raise_for_status()
            data = resp.json()
            raw_json = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_json)
            
            # Format extracted slots safely
            raw_slots = parsed.get("extracted_slots")
            slot_data = BookingSlotData()
            if isinstance(raw_slots, dict):
                for k, v in raw_slots.items():
                    if hasattr(slot_data, k) and v is not None:
                        setattr(slot_data, k, str(v) if not isinstance(v, str) else v)
            parsed["extracted_slots"] = slot_data

            if "assistant_reply" not in parsed and "reply" in parsed:
                parsed["assistant_reply"] = parsed["reply"]

            return AgentInferenceOutput(**parsed)

    @classmethod
    async def _call_gemini(
        cls,
        system_prompt: str,
        history: List[Dict[str, str]],
        message: str
    ) -> Optional[AgentInferenceOutput]:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            contents = []
            for h in history[-8:]:
                role = "model" if h.get("role") in ("assistant", "model") else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h.get("content", ""))]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

            model_name = settings.GEMINI_MODEL
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=AgentInferenceOutput,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            if response.text:
                parsed = json.loads(response.text)
                return AgentInferenceOutput(**parsed)
        except Exception as e:
            logger.debug(f"Gemini call failed: {e}")

        return None

    @classmethod
    async def _call_openai(
        cls,
        system_prompt: str,
        history: List[Dict[str, str]],
        message: str
    ) -> Optional[AgentInferenceOutput]:
        messages = cls._build_openai_messages(system_prompt, history, message)

        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            resp.raise_for_status()
            data = resp.json()
            raw_json = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_json)
            return AgentInferenceOutput(**parsed)

    @classmethod
    async def _call_xai(
        cls,
        system_prompt: str,
        history: List[Dict[str, str]],
        message: str
    ) -> Optional[AgentInferenceOutput]:
        """Call xAI Grok via its OpenAI-compatible API endpoint."""
        messages = cls._build_openai_messages(system_prompt, history, message)

        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.XAI_MODEL,
                    "messages": messages,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            resp.raise_for_status()
            data = resp.json()
            raw_json = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_json)

            raw_slots = parsed.get("extracted_slots")
            slot_data = BookingSlotData()
            if isinstance(raw_slots, dict):
                for k, v in raw_slots.items():
                    if hasattr(slot_data, k) and v is not None:
                        setattr(slot_data, k, str(v) if not isinstance(v, str) else v)
            parsed["extracted_slots"] = slot_data

            if "assistant_reply" not in parsed and "reply" in parsed:
                parsed["assistant_reply"] = parsed["reply"]

            return AgentInferenceOutput(**parsed)

    @classmethod
    def _rule_based_fallback(
        cls,
        user_message: str,
        script_mode: str,
        collected_slots: Dict[str, Any],
        evidence_pack: str,
        is_escalation: bool
    ) -> AgentInferenceOutput:
        """Deterministic rule-based fallback when external LLM APIs are unreachable."""
        msg_lower = user_message.lower().strip()
        fallback_msg = getattr(settings, "RAG_FALLBACK_MESSAGE", "I don't have enough information in the available company knowledge to answer that accurately.")

        if is_escalation:
            if script_mode == "english":
                reply = (
                    "I am so sorry to hear about your experience. We take this very seriously. "
                    "I have escalated this directly to our senior manager who will contact you shortly."
                )
            elif script_mode == "urdu_nastaliq":
                reply = "ہمیں آپ کے تجربے پر بے حد افسوس ہے۔ ہم نے یہ معاملہ سینئر مینیجر کو بھیج دیا ہے، وہ جلد آپ سے رابطہ کریں گے۔"
            else:
                reply = "Hamein aap ke tajurbay par behad afsos hai. Hum ne yeh mamla senior manager ko bhej diya hai, woh jald aap se rabta kareingay."
            
            return AgentInferenceOutput(
                detected_language=script_mode,
                detected_intent="human_escalation",
                requires_human_escalation=True,
                escalation_reason="User frustration or complaint detected",
                confidence_score=0.98,
                assistant_reply=reply
            )

        # Slot Extraction logic
        extracted = BookingSlotData()
        name_match = re.search(r"(?:mera naam|naam mera|name is|i am|this is)\s+([a-zA-Z\s]+?)(?:hai|\.|\,|$)", user_message, re.I)
        if name_match:
            extracted.customer_name = name_match.group(1).strip()

        time_match = re.search(r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|baje))", user_message, re.I)
        if time_match:
            extracted.preferred_time = time_match.group(1).strip()

        date_match = re.search(r"(kal|aaj|parso|today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)", user_message, re.I)
        if date_match:
            extracted.preferred_date = date_match.group(1).strip()

        is_booking = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in ["book", "appointment", "slot", "reserve", "schedule", "karwana", "consultation", "call"])
        is_pricing = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in ["price", "cost", "rate", "fee", "charges", "kitne", "kitna", "pricing", "quote"])
        is_how_are_you = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in ["how are you", "kya haal", "kya hal", "kaise ho", "kesy ho", "kese ho", "theek ho"])
        is_greeting = any(re.search(rf"\b{re.escape(w)}\b", msg_lower) for w in ["salam", "assalam", "asslamualikom", "hello", "hi", "hy", "hey", "aoa", "greetings"]) or is_how_are_you

        intent = "inquiry"
        if is_booking:
            intent = "booking_request"
        elif is_pricing:
            intent = "pricing"
        elif is_greeting:
            intent = "greeting"

        if not evidence_pack or "No matching company knowledge" in evidence_pack:
            reply = fallback_msg
        else:
            # Extract actual answer or body content from the first source
            sources = evidence_pack.split("[SOURCE ")
            extracted_reply = ""
            for s in sources:
                if not s.strip():
                    continue
                lines = s.strip().split("\n")
                content_lines = lines[1:] if len(lines) > 1 else lines
                full_chunk_text = "\n".join(content_lines).strip()
                
                if "A:" in full_chunk_text:
                    parts = full_chunk_text.split("A:", 1)
                    extracted_reply = parts[1].strip()
                    break
                elif full_chunk_text:
                    extracted_reply = full_chunk_text
                    break
            
            reply = extracted_reply or fallback_msg

        return AgentInferenceOutput(
            detected_language=script_mode,
            detected_intent=intent,
            extracted_slots=extracted,
            requires_human_escalation=False,
            confidence_score=0.75,
            assistant_reply=reply
        )
