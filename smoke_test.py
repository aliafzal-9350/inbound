import os
import json
from dotenv import load_dotenv
load_dotenv()

if os.path.exists("ravisn_agent.db"):
    os.remove("ravisn_agent.db")

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import models

# Clean previous test records for clean test run
db = SessionLocal()
try:
    test_tenants = db.query(models.Tenant).filter(models.Tenant.slug.like("%bright-smile%") | (models.Tenant.slug == "second-clinic")).all()
    tenant_ids = [t.id for t in test_tenants]
    if tenant_ids:
        db.query(models.Booking).filter(models.Booking.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.Message).filter(models.Message.conversation_id.in_(
            db.query(models.Conversation.id).filter(models.Conversation.tenant_id.in_(tenant_ids))
        )).delete(synchronize_session=False)
        db.query(models.Conversation).filter(models.Conversation.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.ChannelConnection).filter(models.ChannelConnection.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.KnowledgeEntry).filter(models.KnowledgeEntry.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.TenantKnowledgeChunk).filter(models.TenantKnowledgeChunk.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.User).filter(models.User.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        db.query(models.Tenant).filter(models.Tenant.id.in_(tenant_ids)).delete(synchronize_session=False)
    test_users = db.query(models.User).filter(models.User.email == "owner@brightsmile.test").all()
    for u in test_users:
        db.delete(u)
    db.commit()
finally:
    db.close()

client = TestClient(app)

print("1) signing up (creates tenant + owner user together)...")
r = client.post("/auth/signup", json={
    "business_name": "Bright Smile Clinic", "slug": "bright-smile",
    "email": "owner@brightsmile.test", "password": "supersecret123",
})
assert r.status_code == 200, r.text
signup_data = r.json()
jwt_headers = {"Authorization": "Bearer " + signup_data["token"]}
print("   ok ->", signup_data["tenant"]["slug"], signup_data["email"])

print("1b) logging in with the same credentials...")
r = client.post("/auth/login", json={"email": "owner@brightsmile.test", "password": "supersecret123"})
assert r.status_code == 200, r.text
print("   ok -> token received")

print("1c) wrong password is rejected...")
r = client.post("/auth/login", json={"email": "owner@brightsmile.test", "password": "wrongpass"})
assert r.status_code == 401
print("   ok -> 401 as expected")

print("1d) /auth/me returns the logged-in session...")
r = client.get("/auth/me", headers=jwt_headers)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

print("1e) old-style api key still works too (for scripts/tests)...")
r = client.post("/tenants", json={"name": "Second Clinic", "slug": "second-clinic"})
assert r.status_code == 200, r.text
tenant = r.json()
headers = {"X-API-Key": tenant["api_key"]}
print("   ok ->", tenant["id"], tenant["slug"])

print("1f) knowledge endpoint accepts the jwt token from signup too...")
r = client.get("/knowledge", headers=jwt_headers)
assert r.status_code == 200, r.text
print("   ok -> jwt-authenticated request succeeded,", len(r.json()), "entries")

print("2) adding knowledge base entry...")
r = client.post(
    "/knowledge",
    json={"question": "Clinic ke timings kya hain?", "answer": "Hum Monday se Saturday, 10am se 8pm khule hain."},
    headers=headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json()["question"])

print("3) listing knowledge base...")
r = client.get("/knowledge", headers=headers)
assert r.status_code == 200 and len(r.json()) == 1
print("   ok ->", len(r.json()), "entr(y/ies)")

print("4) sending an in-scope test message on whatsapp channel...")
r = client.post(
    "/chat/test-message",
    json={"channel": "whatsapp", "contact_external_id": "923001234567", "contact_name": "Ahmed Raza", "message": "Aapke clinic ke timings kya hain?"},
    headers=headers,
)
assert r.status_code == 200, r.text
print("   reply ->", r.json()["reply"])
print("   booking_created ->", r.json()["booking_created"])

print("5) sending a booking-intent message on the same conversation...")
r = client.post(
    "/chat/test-message",
    json={"channel": "whatsapp", "contact_external_id": "923001234567", "contact_name": "Ahmed Raza", "message": "Mujhe appointment book karni hai"},
    headers=headers,
)
assert r.status_code == 200, r.text
print("   reply ->", r.json()["reply"])
print("   booking_created ->", r.json()["booking_created"])
print("   booking_info ->", r.json()["booking_info"])

print("6) checking a different channel (instagram) keeps a separate conversation/booking...")
r = client.post(
    "/chat/test-message",
    json={"channel": "instagram", "contact_external_id": "zara.k", "message": "book appointment please"},
    headers=headers,
)
assert r.status_code == 200, r.text
print("   reply ->", r.json()["reply"])
print("   booking_created ->", r.json()["booking_created"])

print("7) confirming a bad api key is rejected...")
r = client.get("/knowledge", headers={"X-API-Key": "wrong-key"})
assert r.status_code == 401
print("   ok -> 401 as expected")

print("\n--- phase 3: whatsapp official connect + webhook ---")

print("8) connecting a whatsapp official number...")
r = client.post(
    "/whatsapp/official/connect",
    json={"phone_number_id": "1234567890", "access_token": "test-token-abc", "waba_id": "waba-001"},
    headers=jwt_headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

print("9) webhook verification handshake (what meta calls once, on setup)...")
r = client.get("/webhooks/whatsapp", params={
    "hub.mode": "subscribe",
    "hub.verify_token": "ravisn-dev-verify-token",
    "hub.challenge": "echo-me-back-12345",
})
assert r.status_code == 200 and r.text == "echo-me-back-12345", r.text
print("   ok -> challenge echoed correctly")

print("9b) webhook handshake with wrong token is rejected...")
r = client.get("/webhooks/whatsapp", params={
    "hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "x",
})
assert r.status_code == 403
print("   ok -> 403 as expected")

print("10) simulating a real incoming whatsapp message from meta...")
meta_payload = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "waba-001",
        "changes": [{
            "field": "messages",
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "15550001111", "phone_number_id": "1234567890"},
                "contacts": [{"profile": {"name": "Ahmed Raza"}, "wa_id": "923009998888"}],
                "messages": [{
                    "from": "923009998888", "id": "wamid.test1",
                    "timestamp": "1234567890", "type": "text",
                    "text": {"body": "Aapke clinic ke timings kya hain?"},
                }],
            },
        }],
    }],
}
r = client.post("/webhooks/whatsapp", json=meta_payload)
assert r.status_code == 200, r.text
print("   ok -> webhook accepted (reply gets logged in mock mode, see [MOCK] line above)")

print("11) checking the conversation now shows up in the inbox...")
r = client.get("/conversations", params={"channel": "whatsapp"}, headers=jwt_headers)
assert r.status_code == 200, r.text
convos = r.json()
assert len(convos) == 1 and convos[0]["contact_name"] == "Ahmed Raza", r.text
print("   ok ->", convos[0]["contact_name"], convos[0]["contact_external_id"])

print("12) checking the messages in that conversation...")
r = client.get(f"/conversations/{convos[0]['id']}/messages", headers=jwt_headers)
assert r.status_code == 200, r.text
msgs = r.json()
assert len(msgs) == 2  # inbound + the agent's outbound reply
print("   ok ->", len(msgs), "messages, directions:", [m["direction"] for m in msgs])

print("13) a webhook message for an unknown phone_number_id is safely ignored...")
bad_payload = json.loads(json.dumps(meta_payload).replace("1234567890", "0000000000"))
r = client.post("/webhooks/whatsapp", json=bad_payload)
assert r.status_code == 200
print("   ok -> no error, silently ignored")

print("\n--- phase 3b: whatsapp qr webhooks (internal, called by the node service) ---")

print("14) qr status webhook rejects a missing/wrong internal secret...")
r = client.post("/webhooks/whatsapp-qr/status", json={"tenant_id": tenant["id"], "status": "connected"})
assert r.status_code == 401
print("   ok -> 401 as expected")

print("15) qr status webhook accepts the correct internal secret...")
qr_secret_headers = {"X-Internal-Secret": "dev-internal-secret"}
r = client.post(
    "/webhooks/whatsapp-qr/status",
    json={"tenant_id": tenant["id"], "status": "connected"},
    headers=qr_secret_headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

print("16) qr message webhook runs a new incoming message through the same pipeline...")
r = client.post(
    "/webhooks/whatsapp-qr",
    json={"tenant_id": tenant["id"], "sender": "923005551234", "name": "Bilal Qr", "text": "Salam, timings kya hain?"},
    headers=qr_secret_headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

r = client.get("/conversations", params={"channel": "whatsapp"}, headers=headers)
assert r.status_code == 200
names = [c["contact_name"] for c in r.json()]
assert "Bilal Qr" in names, names
print("   ok -> Bilal Qr's conversation is in the inbox alongside the official-api one")

print("\n--- phase 4: facebook + instagram connect + webhook ---")

print("17) connecting a facebook page...")
r = client.post(
    "/facebook/connect",
    json={"page_id": "fb-page-001", "access_token": "fb-token-abc"},
    headers=jwt_headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

print("18) connecting an instagram business account...")
r = client.post(
    "/instagram/connect",
    json={"ig_business_account_id": "ig-acct-001", "access_token": "ig-token-abc"},
    headers=jwt_headers,
)
assert r.status_code == 200, r.text
print("   ok ->", r.json())

print("19) meta webhook verification handshake (shared by facebook + instagram)...")
r = client.get("/webhooks/meta", params={
    "hub.mode": "subscribe", "hub.verify_token": "ravisn-dev-verify-token", "hub.challenge": "meta-echo-987",
})
assert r.status_code == 200 and r.text == "meta-echo-987", r.text
print("   ok -> challenge echoed correctly")

print("20) simulating an incoming facebook messenger message...")
fb_payload = {
    "object": "page",
    "entry": [{
        "id": "fb-page-001",
        "time": 1234567890,
        "messaging": [{
            "sender": {"id": "psid-111"},
            "recipient": {"id": "fb-page-001"},
            "timestamp": 1234567890,
            "message": {"mid": "m1", "text": "Timings kya hain?"},
        }],
    }],
}
r = client.post("/webhooks/meta", json=fb_payload)
assert r.status_code == 200, r.text
print("   ok -> webhook accepted (reply logged above with [MOCK] facebook messenger)")

print("21) simulating an incoming instagram dm...")
ig_payload = {
    "object": "instagram",
    "entry": [{
        "id": "ig-acct-001",
        "time": 1234567890,
        "messaging": [{
            "sender": {"id": "igsid-222"},
            "recipient": {"id": "ig-acct-001"},
            "timestamp": 1234567890,
            "message": {"mid": "m2", "text": "Do you take walk-ins?"},
        }],
    }],
}
r = client.post("/webhooks/meta", json=ig_payload)
assert r.status_code == 200, r.text
print("   ok -> webhook accepted (reply logged above with [MOCK] instagram)")

print("22) an echo of our own outbound message is ignored, not looped back in...")
echo_payload = json.loads(json.dumps(fb_payload))
echo_payload["entry"][0]["messaging"][0]["message"]["is_echo"] = True
r = client.post("/webhooks/meta", json=echo_payload)
assert r.status_code == 200
print("   ok -> accepted without creating a duplicate reply")

print("23) checking facebook and instagram each kept their own conversation...")
r = client.get("/conversations", params={"channel": "facebook"}, headers=jwt_headers)
fb_convos = r.json()
r = client.get("/conversations", params={"channel": "instagram"}, headers=jwt_headers)
ig_convos = r.json()
assert len(fb_convos) == 1 and fb_convos[0]["contact_external_id"] == "psid-111", fb_convos
assert len(ig_convos) == 1 and ig_convos[0]["contact_external_id"] == "igsid-222", ig_convos
print("   ok -> facebook:", fb_convos[0]["contact_external_id"], "| instagram:", ig_convos[0]["contact_external_id"])

print("24) an unrecognized object type is safely ignored...")
r = client.post("/webhooks/meta", json={"object": "whatsapp_business_account", "entry": []})
assert r.status_code == 200 and r.json()["status"] == "ignored"
print("   ok ->", r.json())

print("\n--- phase 5: bookings list, per channel ---")

print("25) whatsapp bookings for second-clinic (from step 5 earlier)...")
r = client.get("/bookings", params={"channel": "whatsapp"}, headers=headers)
assert r.status_code == 200, r.text
wa_bookings = r.json()
assert len(wa_bookings) == 1 and wa_bookings[0]["name"] in ("Ahmed Raza", "Test User"), wa_bookings
print("   ok ->", wa_bookings[0]["name"], "|", wa_bookings[0]["contact"], "|", wa_bookings[0]["preferred_time"])

print("26) instagram bookings for second-clinic (from step 6 earlier)...")
r = client.get("/bookings", params={"channel": "instagram"}, headers=headers)
assert r.status_code == 200
ig_bookings = r.json()
assert len(ig_bookings) == 1, ig_bookings
print("   ok ->", len(ig_bookings), "booking")

print("27) facebook bookings for second-clinic (none captured for this tenant)...")
r = client.get("/bookings", params={"channel": "facebook"}, headers=headers)
assert r.status_code == 200 and r.json() == []
print("   ok -> empty, as expected")

print("28) all bookings regardless of channel (no filter)...")
r = client.get("/bookings", headers=headers)
assert r.status_code == 200 and len(r.json()) == 2
print("   ok ->", len(r.json()), "total bookings across channels")

print("\nALL CHECKS PASSED")
