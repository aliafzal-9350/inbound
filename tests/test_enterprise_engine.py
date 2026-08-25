import os
import sys
import unittest
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.redis import RedisService
from app.models.tenant import Tenant
from app.models.knowledge import KnowledgeEntry, TenantKnowledgeChunk
from app.models.conversation import Conversation, Message
from app.models.booking import Booking
from app.schemas.inference import AgentInferenceOutput, BookingSlotData
from app.services.llm_engine import LinguisticNormalizer, LLMEngine
from app.services.rag_engine import HybridRAGEngine
from app.services.state_machine import BookingStateMachine, BookingState
from app.services.calendar_service import CalendarService
from app.services.audio_processor import AudioProcessor
from app.workers.celery_app import celery_app
from app.pipeline import process_incoming_message

celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)



def test_linguistic_normalizer():
    # 1. Roman Urdu Detection
    ru_text = "Salam bhai, mujhe kal sham ko haircut aur beard trim ki appointment chahiye, rate kya hain?"
    assert LinguisticNormalizer.detect_script_mode(ru_text) == "roman_urdu"

    # 2. Nastaliq Urdu Detection
    urdu_text = "وعلیکم السلام، مجھے کل کی اپائنٹمنٹ چاہیے"
    assert LinguisticNormalizer.detect_script_mode(urdu_text) == "urdu_nastaliq"

    # 3. English Detection
    en_text = "Hello, what are your clinic timings and doctor fees?"
    assert LinguisticNormalizer.detect_script_mode(en_text) == "english"

    # 4. Zero-width cleaning
    dirty_text = "Salam\u200B bhai\uFEFF kya haal hai"
    clean = LinguisticNormalizer.clean_text(dirty_text)
    assert "\u200B" not in clean
    assert clean == "Salam bhai kya haal hai"

    # 5. Escalation phrase detection
    assert LinguisticNormalizer.check_escalation_intent("Connect me to human right now!") is True
    assert LinguisticNormalizer.check_escalation_intent("Bande se baat krao meri") is True
    assert LinguisticNormalizer.check_escalation_intent("I want to book an appointment") is False


def test_agent_inference_schema():
    data = {
        "detected_language": "roman_urdu",
        "detected_intent": "booking_request",
        "extracted_slots": {
            "customer_name": "Ali Raza",
            "customer_phone": "+923001234567",
            "service_name": "Haircut & Beard",
            "preferred_date": "2026-08-22",
            "preferred_time": "17:00",
            "notes": None
        },
        "requires_human_escalation": False,
        "escalation_reason": None,
        "confidence_score": 0.96,
        "assistant_reply": "Ji Ali bhai, kal sham 5 baje aap ka slot lock kar diya gaya hai. Koi aur sawal ho to batayein!"
    }
    out = AgentInferenceOutput(**data)
    assert out.detected_language == "roman_urdu"
    assert out.detected_intent == "booking_request"
    assert out.extracted_slots.customer_name == "Ali Raza"
    assert out.confidence_score == 0.96


def test_state_machine_transitions():
    tenant_id = "tenant-test-123"
    user_id = "923009998888"

    # Reset
    BookingStateMachine.reset_session(tenant_id, user_id)

    # Initial state
    slots = BookingStateMachine.get_current_slots(tenant_id, user_id)
    assert slots == {}
    s1 = BookingStateMachine.determine_next_state("IDLE", slots, "greeting")
    assert s1 == BookingState.IDLE.value

    # Partial slots extraction (multi-turn accumulation)
    new_slots = BookingSlotData(service_name="Haircut", customer_name="Ali")
    slots = BookingStateMachine.merge_and_save_slots(tenant_id, user_id, slots, new_slots)
    assert slots["service_name"] == "Haircut"
    assert slots["customer_name"] == "Ali"

    # Next missing slot is phone
    s2 = BookingStateMachine.determine_next_state("COLLECTING_SERVICE", slots, "booking_request")
    assert s2 == BookingState.COLLECTING_PHONE.value

    # Add phone and datetime
    new_slots2 = BookingSlotData(customer_phone="03001234567", preferred_date="2026-08-22", preferred_time="17:00")
    slots = BookingStateMachine.merge_and_save_slots(tenant_id, user_id, slots, new_slots2)
    s3 = BookingStateMachine.determine_next_state(s2, slots, "booking_request")
    assert s3 == BookingState.AWAITING_CONFIRMATION.value


def test_redis_mutex_and_slot_hold():
    tenant_id = "tenant-test"
    slot_iso = "2026-08-22T17:00:00"
    user1 = "user_alpha"
    user2 = "user_beta"

    # User 1 holds slot
    hold1 = CalendarService.hold_slot(tenant_id, slot_iso, user1)
    assert hold1 is True

    # User 2 tries to hold the same slot -> should fail
    hold2 = CalendarService.hold_slot(tenant_id, slot_iso, user2)
    assert hold2 is False

    # User 1 releases hold
    RedisService.release_slot_hold(tenant_id, slot_iso)
    # Now User 2 can hold
    hold3 = CalendarService.hold_slot(tenant_id, slot_iso, user2)
    assert hold3 is True
    RedisService.release_slot_hold(tenant_id, slot_iso)


def test_hybrid_rag_and_evidence_pack():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    tenant = Tenant(business_name="Elite Grooming Lounge", slug="elite-grooming")
    db.add(tenant)
    db.commit()

    chunk1 = TenantKnowledgeChunk(
        tenant_id=tenant.id,
        category="Pricing",
        chunk_title="Haircut & Beard Rates",
        chunk_content="Haircut charges are PKR 1,000 and Beard trim is PKR 500. Total combo is PKR 1,500."
    )
    chunk2 = TenantKnowledgeChunk(
        tenant_id=tenant.id,
        category="Timings",
        chunk_title="Business Hours",
        chunk_content="We are open Monday to Saturday from 10:00 AM to 8:00 PM."
    )
    db.add_all([chunk1, chunk2])
    db.commit()

    results = HybridRAGEngine.search(db, tenant.id, "haircut and beard price rate", top_k=2)
    assert len(results) >= 1
    assert "Haircut" in results[0]["content"] or "PKR 1,500" in results[0]["content"]

    evidence_pack = HybridRAGEngine.build_evidence_pack(results)
    assert "[SOURCE 1]" in evidence_pack
    assert "Haircut" in evidence_pack
    db.close()


def test_end_to_end_pipeline_flow():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    tenant = Tenant(business_name="Royal Salon", slug="royal-salon")
    db.add(tenant)
    db.commit()

    # Step 1: Inbound message in Roman Urdu
    res1 = process_incoming_message(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id="923001112233",
        contact_name="Ahmed",
        message_text="Salam bhai, timings kya hain?"
    )
    assert res1["reply"] is not None
    assert res1["detected_language"] == "roman_urdu"

    # Step 2: Inbound escalation message
    res2 = process_incoming_message(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id="923001112233",
        contact_name="Ahmed",
        message_text="Your staff was extremely rude and ruined my hair. Connect me to human manager right now!"
    )
    assert res2["is_escalated"] is True
    assert res2["fsm_state"] == BookingState.ESCALATED.value

    db.close()


from app.services.intent_router import is_pure_greeting


def test_intent_gating_zero_rag_bypass():
    """Phase 1: Intent Gating Before Retrieval (Zero-RAG Bypass)."""
    # Pure pleasantries (Must evaluate to True)
    assert is_pure_greeting("Asslamualikom") is True
    assert is_pure_greeting("Assalamualaykum") is True
    assert is_pure_greeting("Salam") is True
    assert is_pure_greeting("salam bhai") is True
    assert is_pure_greeting("How are you ali") is True
    assert is_pure_greeting("Kya haal hai") is True
    assert is_pure_greeting("Kaise ho") is True
    assert is_pure_greeting("Hello") is True
    assert is_pure_greeting("Hi") is True
    assert is_pure_greeting("Good morning") is True
    assert is_pure_greeting("Aoa") is True

    # Explicit inquiries (Must evaluate to False to allow RAG retrieval & intent action)
    assert is_pure_greeting("Salam timings kya hain?") is False
    assert is_pure_greeting("Asslamualikom mujhe haircut price chahiye") is False
    assert is_pure_greeting("Hello I want to book an appointment") is False
    assert is_pure_greeting("What are your doctor charges?") is False
    assert is_pure_greeting("Timing kya hai aapki?") is False


def test_persona_and_zero_rag_multi_turn_flow():
    """Phase 2, Phase 4 & Phase 5: Multi-Turn Conversation & Persona Rules."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    tenant = Tenant(business_name="Royal Salon", slug="royal-salon")
    db.add(tenant)
    db.commit()

    chunk = TenantKnowledgeChunk(
        tenant_id=tenant.id,
        category="Timings",
        chunk_title="Store Hours",
        chunk_content="We are open Monday to Saturday from 10:00 AM to 8:00 PM."
    )
    db.add(chunk)
    db.commit()

    # Turn 1: Pure greeting -> Zero-RAG Bypass, warm reply, no business hours or booking push
    res1 = process_incoming_message(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id="92300998877",
        contact_name="Ali",
        message_text="Asslamualikom"
    )
    reply1 = res1["reply"].lower()
    assert "walaikum" in reply1 or "assalam" in reply1 or "madad" in reply1 or "help" in reply1
    # Must NOT dump store hours on turn 1
    assert "10:00" not in reply1 and "8:00" not in reply1
    # Must keep greetings short (under 25 words)
    assert len(res1["reply"].split()) <= 25

    # Turn 2: Chitchat / Status question
    res2 = process_incoming_message(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id="92300998877",
        contact_name="Ali",
        message_text="How are you ali"
    )
    reply2 = res2["reply"].lower()
    assert "theek" in reply2 or "doing great" in reply2 or "madad" in reply2 or "help" in reply2
    # Must NOT dump store hours on greeting turn
    assert "10:00" not in reply2 and "8:00" not in reply2
    assert len(res2["reply"].split()) <= 25

    # Turn 3: Explicit timing inquiry -> RAG returns business hours
    res3 = process_incoming_message(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id="92300998877",
        contact_name="Ali",
        message_text="Timing kya hai aapki?"
    )
    reply3 = res3["reply"]
    assert "10" in reply3 or "Monday" in reply3 or "open" in reply3 or "subah" in reply3

    db.close()


def test_semantic_thresholding_and_ungrounded_fallback():
    """Phase 3: Semantic Thresholding and Ungrounded Fallback."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    tenant = Tenant(business_name="Dental Care", slug="dental-care")
    db.add(tenant)
    db.commit()

    # Search for completely unrelated query that has no match
    results = HybridRAGEngine.search(db, tenant.id, "international rocket spaceship flight", top_k=2)
    assert len(results) == 0

    evidence_pack = HybridRAGEngine.build_evidence_pack(results)
    assert evidence_pack == ""

    # Rule-based fallback on ungrounded inquiry
    fb = LLMEngine._rule_based_fallback(
        "Do you have spaceship rockets?",
        "english",
        {},
        evidence_pack,
        False
    )
    assert "I don't have that specific information in my records right now, but I can connect you with our team." in fb.assistant_reply
    db.close()


def test_dynamic_rag_services_and_pricing_queries():
    """Verify Section 5 test matrix: Purging static templates for Qwen & Dynamic RAG."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine)
    db = TestSession()

    tenant = Tenant(business_name="Luxe Salon & Spa", slug="luxe-salon")
    db.add(tenant)
    db.commit()

    chunk1 = TenantKnowledgeChunk(
        tenant_id=tenant.id,
        category="Services",
        chunk_title="Salon Services",
        chunk_content="We offer Haircut, Beard trim, Facial, and Hair Styling treatments."
    )
    chunk2 = TenantKnowledgeChunk(
        tenant_id=tenant.id,
        category="Pricing",
        chunk_title="Service Rates",
        chunk_content="Haircut charges are PKR 1,000 and Beard trim is PKR 500. Total combo is PKR 1,500."
    )
    db.add_all([chunk1, chunk2])
    db.commit()

    # Case 1: "What is your services" -> Lists actual company services retrieved from chunks
    res1 = process_incoming_message(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="92311223344", contact_name="Sara",
        message_text="What is your services"
    )
    reply1 = res1["reply"]
    assert "Haircut" in reply1 or "Beard" in reply1 or "offer" in reply1
    assert "How can I assist you with our services today?" not in reply1

    # Case 2: "Which services you offer" -> Lists company offerings and asks which one user is interested in
    res2 = process_incoming_message(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="92311223344", contact_name="Sara",
        message_text="Which services you offer"
    )
    reply2 = res2["reply"]
    assert ("Haircut" in reply2 or "offer" in reply2) and ("interested" in reply2 or "which" in reply2 or "service" in reply2)

    # Case 3: "price kya hai haircut ki?" -> Returns verified pricing in Roman Urdu using retrieved chunk
    res3 = process_incoming_message(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="92311223344", contact_name="Sara",
        message_text="price kya hai haircut ki?"
    )
    reply3 = res3["reply"]
    assert "1,000" in reply3 or "1000" in reply3 or "PKR" in reply3 or "500" in reply3

    # Case 4: "Asslamualikom" -> Warm greeting, no store hours dumped
    res4 = process_incoming_message(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="92311223344", contact_name="Sara",
        message_text="Asslamualikom"
    )
    reply4 = res4["reply"].lower()
    assert "walaikum" in reply4 or "assalam" in reply4 or "madad" in reply4
    assert "10:00" not in reply4 and "monday" not in reply4

    # Case 5: "How are you ali" -> Polite status reply, no store hours dumped
    res5 = process_incoming_message(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="92311223344", contact_name="Sara",
        message_text="How are you ali"
    )
    reply5 = res5["reply"].lower()
    assert "theek" in reply5 or "doing great" in reply5 or "madad" in reply5 or "help" in reply5
    assert "10:00" not in reply5 and "monday" not in reply5

    db.close()


if __name__ == "__main__":
    print("Running Linguistic Normalizer Tests...")
    test_linguistic_normalizer()
    print("Running Intent Gating Zero-RAG Bypass Tests (Phase 1)...")
    test_intent_gating_zero_rag_bypass()
    print("Running Agent Inference Schema Tests (Phase 5)...")
    test_agent_inference_schema()
    print("Running State Machine Transition Tests...")
    test_state_machine_transitions()
    print("Running Redis Mutex & Slot Hold Tests...")
    test_redis_mutex_and_slot_hold()
    print("Running Hybrid RAG & Evidence Pack Tests...")
    test_hybrid_rag_and_evidence_pack()
    print("Running Semantic Thresholding & Ungrounded Tests (Phase 3)...")
    test_semantic_thresholding_and_ungrounded_fallback()
    print("Running Multi-Turn & Persona Rules Tests (Phase 2 & Phase 4)...")
    test_persona_and_zero_rag_multi_turn_flow()
    print("Running Dynamic RAG Services & Pricing Queries Tests (Section 5 Matrix)...")
    test_dynamic_rag_services_and_pricing_queries()
    print("Running End-to-End Pipeline Tests...")
    test_end_to_end_pipeline_flow()
    print("\n>>> ALL ENTERPRISE ROADMAP & QWEN RAG TESTS PASSED SUCCESSFULLY! <<<")



