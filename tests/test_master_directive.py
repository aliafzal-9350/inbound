import asyncio
import json
from app.core.database import SessionLocal
from app.models import Tenant, DemoBooking, Booking
from app.pipeline import process_incoming_message_async

async def run_master_directive_test():
    db = SessionLocal()
    tenant = db.query(Tenant).first()

    print("==================================================")
    print("TEST 1: SMALL TALK & PERSONA CHECKS ('Ravi')")
    print("==================================================")

    # 1. "how are you"
    uid1 = "test_user_smalltalk_1"
    res1 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=uid1, contact_name="Guest",
        message_text="how are you"
    )
    print(f"\n[User]: 'how are you'\n[Bot]: {res1['reply']}")
    assert "ravi" in res1["reply"].lower() or "doing great" in res1["reply"].lower(), "Failed small talk response"

    # 2. "asslamulikom"
    uid2 = "test_user_smalltalk_2"
    res2 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=uid2, contact_name="Guest",
        message_text="asslamulikom"
    )
    print(f"\n[User]: 'asslamulikom'\n[Bot]: {res2['reply']}")
    assert "walaikum assalam" in res2["reply"].lower() and "ravi" in res2["reply"].lower(), "Failed Islamic greeting response"

    # 3. "who are you"
    uid3 = "test_user_smalltalk_3"
    res3 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=uid3, contact_name="Guest",
        message_text="who are you"
    )
    print(f"\n[User]: 'who are you'\n[Bot]: {res3['reply']}")
    assert "ravi" in res3["reply"].lower() and "ravisn" in res3["reply"].lower(), "Failed identity response"

    print("\n==================================================")
    print("TEST 2: MULTI-TURN BOOKING & MEMORY RECALL TEST")
    print("==================================================")

    lead_uid = "test_lead_tahir_99"

    # Turn 1: Trigger Demo
    print("\n[Turn 1] User: 'I want a demo'")
    r1 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=lead_uid, contact_name="Tahir",
        message_text="I want a demo"
    )
    print("Bot Reply:", json.dumps(r1["reply"], ensure_ascii=True))

    # Turn 2: Industry
    print("\n[Turn 2] User: 'HVAC'")
    r2 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=lead_uid, contact_name="Tahir",
        message_text="HVAC"
    )
    print("Bot Reply:", json.dumps(r2["reply"], ensure_ascii=True))

    # Turn 3: Name & Email
    print("\n[Turn 3] User: 'Tahir tahir@example.com'")
    r3 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=lead_uid, contact_name="Tahir",
        message_text="Tahir tahir@example.com"
    )
    print("Bot Reply:", json.dumps(r3["reply"], ensure_ascii=True))

    # Turn 4: Service
    print("\n[Turn 4] User: 'WhatsApp Automation'")
    r4 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=lead_uid, contact_name="Tahir",
        message_text="WhatsApp Automation"
    )
    print("Bot Reply:", json.dumps(r4["reply"], ensure_ascii=True))

    # Turn 5: Memory Recall / Review
    print("\n[Turn 5] User: 'give me the detail which i share with you'")
    r5 = await process_incoming_message_async(
        db=db, tenant=tenant, channel="whatsapp",
        contact_external_id=lead_uid, contact_name="Tahir",
        message_text="give me the detail which i share with you"
    )
    print("Bot Reply:", json.dumps(r5["reply"], ensure_ascii=True))

    print("\n==================================================")
    print("TEST 3: DATABASE RECORD VALIDATION")
    print("==================================================")

    demo_rec = db.query(DemoBooking).filter(DemoBooking.phone_number == lead_uid).order_by(DemoBooking.created_at.desc()).first()
    assert demo_rec is not None, "DemoBooking record not found!"
    print(f"DemoBooking ID: {demo_rec.id}")
    print(f"Name: {demo_rec.name}")
    print(f"Email: {demo_rec.email}")
    print(f"Industry: {demo_rec.industry}")
    print(f"Service Needed: {demo_rec.service_needed}")
    print(f"Status: {demo_rec.status}")

    assert demo_rec.name == "Tahir", f"Expected name Tahir, got {demo_rec.name}"
    assert demo_rec.email == "tahir@example.com", f"Expected email tahir@example.com, got {demo_rec.email}"
    assert demo_rec.industry == "Hvac", f"Expected industry Hvac, got {demo_rec.industry}"
    assert demo_rec.service_needed == "WhatsApp Automation", f"Expected service WhatsApp Automation, got {demo_rec.service_needed}"

    print("\nALL VERIFICATIONS PASSED 100% PERFECTLY!")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_master_directive_test())
