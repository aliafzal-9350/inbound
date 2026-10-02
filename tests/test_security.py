"""Multi-business security: authentication, owner-only settings, isolation between businesses."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import models
from app.core.database import SessionLocal
from app.main import app
from app.security import hash_password

OWNER_EMAIL = "ravisn.uk@gmail.com"
OWNER_PASSWORD = "Owner-pass-123"
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def owner_account():
    db = SessionLocal()
    if not db.query(models.User).filter(models.User.email == OWNER_EMAIL).first():
        tenant = models.Tenant(business_name="RAVISN UK", name="RAVISN UK", slug="ravisn-uk")
        db.add(tenant)
        db.flush()
        db.add(models.User(tenant_id=tenant.id, email=OWNER_EMAIL, hashed_password=hash_password(OWNER_PASSWORD)))
        db.commit()
    db.close()


def login(email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


def bearer(email, password):
    resp = login(email, password)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def new_client_account():
    email = f"client-{uuid.uuid4().hex[:8]}@business.com"
    resp = client.post("/auth/signup", json={"business_name": "Smile Clinic", "slug": "smile", "email": email,
                                             "password": "Client-pass-1"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_platform_admin"] is False
    return email, {"Authorization": f"Bearer {resp.json()['token']}"}, resp.json()["tenant"]["id"]


# ---------------------------------------------------------------- authentication
@pytest.mark.parametrize("path", ["/conversations", "/bookings", "/knowledge", "/channels", "/settings/api-keys",
                                  "/settings/notifications", "/settings/system-prompt", "/api/conversations"])
def test_anonymous_requests_are_rejected(path):
    assert client.get(path).status_code == 401


def test_owner_needs_the_real_password():
    assert login(OWNER_EMAIL, "anything-at-all").status_code == 401
    resp = login(OWNER_EMAIL, OWNER_PASSWORD)
    assert resp.status_code == 200 and resp.json()["is_platform_admin"] is True


def test_signup_with_an_existing_email_does_not_log_in():
    resp = client.post("/auth/signup", json={"business_name": "X", "slug": "x", "email": OWNER_EMAIL,
                                             "password": "whatever-123"})
    assert resp.status_code == 409 and "token" not in resp.json()


def test_public_password_reset_is_gone():
    resp = client.post("/auth/reset-password", json={"email": OWNER_EMAIL, "new_password": "hijacked-123"})
    assert resp.status_code in (404, 405)
    assert login(OWNER_EMAIL, OWNER_PASSWORD).status_code == 200


def test_signup_rejects_short_passwords_and_bad_emails():
    assert client.post("/auth/signup", json={"business_name": "A", "slug": "a", "email": "new@biz.com",
                                             "password": "short"}).status_code == 400
    assert client.post("/auth/signup", json={"business_name": "A", "slug": "a", "email": "not-an-email",
                                             "password": "long-enough-1"}).status_code == 400


def test_repeated_wrong_passwords_are_throttled():
    email, _, _ = new_client_account()
    for _ in range(10):
        assert login(email, "wrong-password").status_code == 401
    assert login(email, "Client-pass-1").status_code == 429


def test_change_password_requires_the_current_one():
    email, headers, _ = new_client_account()
    assert client.post("/auth/change-password", headers=headers,
                       json={"current_password": "wrong", "new_password": "Brand-new-pass"}).status_code == 400
    assert client.post("/auth/change-password", headers=headers,
                       json={"current_password": "Client-pass-1", "new_password": "Brand-new-pass"}).status_code == 200
    assert login(email, "Brand-new-pass").status_code == 200


# ---------------------------------------------------------------- owner-only platform settings
def test_clients_cannot_see_or_change_platform_ai_keys():
    _, headers, _ = new_client_account()
    assert client.get("/settings/api-keys", headers=headers).status_code == 403
    assert client.get("/settings/api-key", headers=headers).status_code == 403
    assert client.post("/settings/api-keys/groq", headers=headers, json={"api_key": "gsk_evil"}).status_code == 403
    assert client.delete("/settings/api-keys/groq", headers=headers).status_code == 403
    assert client.post("/settings/api-key", headers=headers, json={"openai_api_key": "gsk_evil"}).status_code == 403


def test_owner_can_manage_platform_ai_keys():
    headers = bearer(OWNER_EMAIL, OWNER_PASSWORD)
    resp = client.get("/settings/api-keys", headers=headers)
    assert resp.status_code == 200 and "groq" in resp.json()


def test_workspace_creation_api_is_owner_only():
    _, headers, _ = new_client_account()
    payload = {"name": "Sneaky", "slug": f"sneaky-{uuid.uuid4().hex[:6]}"}
    assert client.post("/tenants", json=payload).status_code == 401
    assert client.post("/tenants", headers=headers, json=payload).status_code == 403
    assert client.post("/tenants", headers=bearer(OWNER_EMAIL, OWNER_PASSWORD), json=payload).status_code == 200


def test_only_the_owner_can_reset_a_clients_password():
    email, headers, _ = new_client_account()
    body = {"email": email, "new_password": "Temporary-123"}
    assert client.post("/auth/admin/reset-password", json=body).status_code == 401
    assert client.post("/auth/admin/reset-password", headers=headers, json=body).status_code == 403
    assert client.post("/auth/admin/reset-password", headers=bearer(OWNER_EMAIL, OWNER_PASSWORD),
                       json=body).status_code == 200
    assert login(email, "Temporary-123").status_code == 200


def test_me_reports_owner_flag():
    assert client.get("/auth/me", headers=bearer(OWNER_EMAIL, OWNER_PASSWORD)).json()["is_platform_admin"] is True
    _, headers, _ = new_client_account()
    assert client.get("/auth/me", headers=headers).json()["is_platform_admin"] is False


# ---------------------------------------------------------------- isolation between businesses
def test_placeholder_default_bookings_are_not_shown_to_anyone():
    db = SessionLocal()
    db.add(models.Booking(tenant_id="default", name="Someone Else", contact="x@y.com", status="pending"))
    db.commit()
    db.close()
    _, headers, _ = new_client_account()
    bookings = client.get("/bookings", headers=headers).json()
    assert all(b.get("name") != "Someone Else" for b in bookings)


def test_a_page_cannot_be_connected_to_two_businesses():
    _, headers_a, _ = new_client_account()
    _, headers_b, _ = new_client_account()
    page = f"page-{uuid.uuid4().hex[:8]}"
    assert client.post("/facebook/connect", headers=headers_a,
                       json={"page_id": page, "access_token": "token-a"}).status_code == 200
    assert client.post("/facebook/connect", headers=headers_b,
                       json={"page_id": page, "access_token": "token-b"}).status_code == 409


def _meta_event(page_id):
    return {"object": "page", "entry": [{"id": page_id, "messaging": [
        {"sender": {"id": "customer-1"}, "message": {"mid": f"m_{uuid.uuid4().hex}", "text": "Hi"}}]}]}


def test_webhooks_only_reach_the_exact_page_owner():
    _, headers_a, tenant_a = new_client_account()
    page = f"page-{uuid.uuid4().hex[:8]}"
    client.post("/facebook/connect", headers=headers_a, json={"page_id": page, "access_token": "token-a"})

    with patch("app.routers.meta_messaging.pipeline.process_incoming_message_async",
               new=AsyncMock(return_value={"reply": "hello"})) as pipeline_call, \
         patch("app.routers.meta_messaging.MetaGateway.send_facebook_message", new=AsyncMock()), \
         patch("app.routers.meta_messaging.MetaGateway.send_typing_indicator", new=AsyncMock()):
        assert client.post("/webhooks/meta", json=_meta_event("some-other-businesses-page")).status_code == 200
        assert pipeline_call.await_count == 0          # unknown page: ignored, never routed elsewhere

        assert client.post("/webhooks/meta", json=_meta_event(page)).status_code == 200
        assert pipeline_call.await_count == 1
        assert str(pipeline_call.await_args.kwargs["tenant"].id) == tenant_a

        client.post("/channels/facebook/disconnect", headers=headers_a)
        assert client.post("/webhooks/meta", json=_meta_event(page)).status_code == 200
        assert pipeline_call.await_count == 1          # disconnected page: no longer answered


# ---------------------------------------------------------------- per-business alerts
@pytest.mark.parametrize("url", ["http://hooks.example.com/x", "https://localhost/x", "https://127.0.0.1/x",
                                 "https://169.254.169.254/latest/meta-data", "https://10.0.0.5/hook",
                                 "https://user:pass@hooks.example.com/x"])
def test_alert_webhook_must_be_a_public_https_url(url):
    _, headers, _ = new_client_account()
    assert client.post("/settings/notifications", headers=headers, json={"alert_webhook_url": url}).status_code == 400


def test_business_can_set_and_clear_its_alert_webhook():
    _, headers, _ = new_client_account()
    with patch("app.core.url_safety.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]):
        resp = client.post("/settings/notifications", headers=headers,
                           json={"alert_webhook_url": "https://hooks.slack.com/services/T/B/X"})
    assert resp.status_code == 200
    assert client.get("/settings/notifications", headers=headers).json()["alert_webhook_url"].startswith("https://")
    assert client.post("/settings/notifications", headers=headers,
                       json={"alert_webhook_url": ""}).json()["alert_webhook_url"] is None


def test_escalation_alerts_go_to_each_business_not_the_platform():
    from app.workers.tasks import dispatch_escalation_alert
    _, _, client_tenant = new_client_account()
    db = SessionLocal()
    owner_tenant = db.query(models.User).filter(models.User.email == OWNER_EMAIL).one().tenant_id
    db.close()
    public = [(2, 1, 6, "", ("93.184.216.34", 443))]

    with patch("app.workers.tasks.httpx.post", return_value=MagicMock(status_code=200)) as post, \
         patch("app.core.url_safety.socket.getaddrinfo", return_value=public):
        dispatch_escalation_alert(client_tenant, "customer-1", "I want a human", "Customer asked for a human")
        assert post.call_count == 0                     # client has no webhook: never sent to the platform's

        db = SessionLocal()
        db.query(models.Tenant).filter(models.Tenant.id == client_tenant).update(
            {"alert_webhook_url": "https://client-business.example/hook"})
        db.commit()
        db.close()
        dispatch_escalation_alert(client_tenant, "customer-1", "I want a human", "Customer asked for a human")
        assert post.call_args.args[0] == "https://client-business.example/hook"

        dispatch_escalation_alert(owner_tenant, "customer-2", "help", "Customer asked for a human")
        assert post.call_args.args[0] == "https://platform-owner.example/alerts"
