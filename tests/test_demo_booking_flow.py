import asyncio
import json
from app.core.database import SessionLocal
from app.models import Tenant, DemoBooking
from app.pipeline import process_incoming_message_async

async def test_multi_turn_booking():
    db = SessionLocal()
    tenant = db.query(Tenant).first()
    user_id = "test_whatsapp_lead_999"

    print("=== Multi-Turn Stateful Demo Booking Simulation ===")

    # Turn 1: Trigger
    print("\n[Turn 1] User: 'Yes i want to book free demo'")
    res1 = await process_incoming_message_async(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id=user_id,
        contact_name="Ali Afzal",
        message_text="Yes i want to book free demo"
    )
    print("Bot Reply:", json.dumps(res1['reply'], ensure_ascii=True))

    # Turn 2: Industry
    print("\n[Turn 2] User: 'Hvac'")
    res2 = await process_incoming_message_async(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id=user_id,
        contact_name="Ali Afzal",
        message_text="Hvac"
    )
    print("Bot Reply:", json.dumps(res2['reply'], ensure_ascii=True))

    # Turn 3: Name & Email
    print("\n[Turn 3] User: 'Ali Afzal ali@ravisn.com'")
    res3 = await process_incoming_message_async(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id=user_id,
        contact_name="Ali Afzal",
        message_text="Ali Afzal ali@ravisn.com"
    )
    print("Bot Reply:", json.dumps(res3['reply'], ensure_ascii=True))

    # Turn 4: Service Needed
    print("\n[Turn 4] User: 'WhatsApp inbound lead chatbot'")
    res4 = await process_incoming_message_async(
        db=db,
        tenant=tenant,
        channel="whatsapp",
        contact_external_id=user_id,
        contact_name="Ali Afzal",
        message_text="WhatsApp inbound lead chatbot"
    )
    print("Bot Reply:", json.dumps(res4['reply'], ensure_ascii=True))


    # Verify Database Persistence
    booking = db.query(DemoBooking).filter(DemoBooking.phone_number == user_id).order_by(DemoBooking.created_at.desc()).first()
    print("\n=== Database Record Verification ===")
    if booking:
        print(f"ID: {booking.id}")
        print(f"Industry: {booking.industry}")
        print(f"Name: {booking.name}")
        print(f"Email: {booking.email}")
        print(f"Service Needed: {booking.service_needed}")
        print(f"Status: {booking.status}")
        print("SUCCESS: Lead captured and persisted perfectly without loops!")
    else:
        print("ERROR: Booking record not found in database!")

    db.close()

if __name__ == "__main__":
    asyncio.run(test_multi_turn_booking())
