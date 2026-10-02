import os
import json
import logging
import asyncio
import httpx
from .celery_app import celery_app
from ..core.config import settings
from ..core.database import SessionLocal
from ..models.tenant import Tenant
from ..models.conversation import Conversation
from ..models.booking import Booking

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.dispatch_escalation_alert")
def dispatch_escalation_alert(tenant_id: str, customer_phone: str, summary: str, reason: str):
    """Posts a "customer wants a human" alert to the business's OWN webhook (Settings > Notifications).
    The platform-wide STAFF_ESCALATION_WEBHOOK_URL only ever receives the platform owner's own alerts,
    never another business's customers."""
    from ..auth import is_platform_admin
    from ..core.url_safety import public_https_url_error

    logger.info(f"[ESCALATION TRIGGERED] Tenant: {tenant_id}, Customer: {customer_phone}, Reason: {reason}")
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return
        business = tenant.business_name or tenant.name or "your business"
        webhook_url = tenant.alert_webhook_url
        if not webhook_url and any(is_platform_admin(u) for u in tenant.users):
            webhook_url = settings.STAFF_ESCALATION_WEBHOOK_URL
    finally:
        db.close()

    if not webhook_url:
        logger.info(f"No alert webhook configured for tenant {tenant_id}; escalation visible in the dashboard only")
        return
    if webhook_url != settings.STAFF_ESCALATION_WEBHOOK_URL:
        error = public_https_url_error(webhook_url)   # re-checked at send time: DNS may have changed
        if error:
            logger.warning(f"Refusing alert webhook for tenant {tenant_id}: {error}")
            return
    text = (f"🚨 Customer wants to talk to a person - {business}\n"
            f"Customer: {customer_phone}\nReason: {reason}\nMessage: {summary}")
    try:
        resp = httpx.post(webhook_url, timeout=5.0, follow_redirects=False, json={
            "text": text, "content": text,   # Slack uses "text", Discord uses "content"
            "business": business, "customer": customer_phone, "reason": reason, "message": summary,
        })
        logger.info(f"Escalation webhook status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to post escalation to webhook: {e}")

    staff_number = settings.STAFF_WHATSAPP_NUMBER
    if staff_number:
        logger.info(f"Alerting staff WhatsApp number: {staff_number}")


@celery_app.task(name="app.workers.tasks.sync_calendar_event")
def sync_calendar_event(booking_id: str):
    """Background synchronization for booking calendar events."""
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return
        logger.info(f"Syncing calendar event for booking: {booking.id} - {booking.service_name}")
    finally:
        db.close()
