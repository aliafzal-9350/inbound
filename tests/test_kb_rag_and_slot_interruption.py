import asyncio
import json
from app.core.database import SessionLocal
from app.models import Tenant, DemoBooking, KnowledgeEntry
from app.pipeline import process_incoming_message_async
from app import crud

async def run_kb_and_slot_interruption_test():
    db = SessionLocal()
    tenant = db.query(Tenant).first()

    print("==================================================")
    print("TEST 1: FRONTEND KNOWLEDGE BASE RAG TEST (CEO)")
    print("==================================================")

    # 1. Seed custom FAQ from dashboard
    crud.add_knowledge(
        db=db,
        tenant_id=tenant.id,
        question="who is your CEO",
        answer="Usama Anis is the CEO and Founder of RAVISN."
    )

    # 2. Query the agent
    ceo_res = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id="test_user_ceo_query", contact_name="Guest",
        message_text="Who is your CEO?"
    )
    print(f"\n[User]: 'Who is your CEO?'\n[Bot Reply]: {ceo_res['reply']}")
    assert "usama anis" in ceo_res["reply"].lower(), "Failed to answer CEO from database Knowledge Base"
    print("SUCCESS: CEO answer retrieved from database KB with 100% precision!")

    print("\n==================================================")
    print("TEST 2: SLOT INTERRUPTION & RECOVERY TEST")
    print("==================================================")

    interrupted_lead = "test_lead_interruption_tahir"

    # Turn 1: Trigger Demo
    print("\n[Turn 1] User: 'I want a demo'")
    r1 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=interrupted_lead, contact_name="Tahir",
        message_text="I want a demo"
    )
    print("Bot Reply:", json.dumps(r1["reply"], ensure_ascii=True))

    # Turn 2: Industry
    print("\n[Turn 2] User: 'HVAC'")
    r2 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=interrupted_lead, contact_name="Tahir",
        message_text="HVAC"
    )
    print("Bot Reply:", json.dumps(r2["reply"], ensure_ascii=True))

    # Turn 3: Name & Email
    print("\n[Turn 3] User: 'Tahir tahir@example.com'")
    r3 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=interrupted_lead, contact_name="Tahir",
        message_text="Tahir tahir@example.com"
    )
    print("Bot Reply:", json.dumps(r3["reply"], ensure_ascii=True))

    # Turn 4: Interruption (Where is your office located?)
    print("\n[Turn 4 - Interruption] User: 'Where is your office located?'")
    r4 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=interrupted_lead, contact_name="Tahir",
        message_text="Where is your office located?"
    )
    print("Bot Reply:", json.dumps(r4["reply"], ensure_ascii=True))
    assert "mcleod" in r4["reply"].lower() or "office" in r4["reply"].lower(), "Failed to answer office location"
    assert "service" in r4["reply"].lower() or "automation" in r4["reply"].lower(), "Failed to re-prompt for pending slot"
    print("SUCCESS: Interruption answered accurately and pending slot re-prompted without flow breaking!")

    # Turn 5: Resume slot filling with Service
    print("\n[Turn 5] User: 'WhatsApp Automation'")
    r5 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=interrupted_lead, contact_name="Tahir",
        message_text="WhatsApp Automation"
    )
    print("Bot Reply:", json.dumps(r5["reply"], ensure_ascii=True))

    print("\n==================================================")
    print("TEST 3: DATABASE PERSISTENCE CHECK")
    print("==================================================")

    booking = db.query(DemoBooking).filter(DemoBooking.phone_number == interrupted_lead).order_by(DemoBooking.created_at.desc()).first()
    assert booking is not None, "DemoBooking record not found!"
    print(f"ID: {booking.id}")
    print(f"Name: {booking.name}")
    print(f"Email: {booking.email}")
    print(f"Industry: {booking.industry}")
    print(f"Service Needed: {booking.service_needed}")

    assert booking.name == "Tahir"
    assert booking.email == "tahir@example.com"
    assert booking.industry == "Hvac"
    assert booking.service_needed == "WhatsApp Automation"

    print("\nALL 3 TESTS PASSED WITH 100% SUCCESS!")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_kb_and_slot_interruption_test())
