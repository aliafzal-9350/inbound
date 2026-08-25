import os
import httpx

def _get_url() -> str:
    return os.getenv("WHATSAPP_QR_SERVICE_URL") or "http://whatsapp-qr-service:3001"


def start_session(tenant_id: str) -> dict:
    resp = httpx.post(f"{_get_url()}/sessions/{tenant_id}/start", timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_status(tenant_id: str) -> dict:
    resp = httpx.get(f"{_get_url()}/sessions/{tenant_id}/status", timeout=10)
    resp.raise_for_status()
    return resp.json()


def send_message(tenant_id: str, to: str, body: str) -> dict:
    resp = httpx.post(
        f"{_get_url()}/sessions/{tenant_id}/send",
        json={"to": to, "body": body},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def disconnect_session(tenant_id: str) -> dict:
    resp = httpx.delete(f"{_get_url()}/sessions/{tenant_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()
