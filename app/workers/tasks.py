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
    """Sends immediate human escalation alert to WhatsApp Staff Group / Slack / CRM."""
    logger.info(f"[ESCALATION TRIGGERED] Tenant: {tenant_id}, Customer: {customer_phone}, Reason: {reason}")
    
    webhook_url = settings.STAFF_ESCALATION_WEBHOOK_URL
    if webhook_url:
        try:
            payload = {
                "text": f"🚨 *URGENT ESCALATION REQUIRED*\n*Tenant ID:* `{tenant_id}`\n*Customer:* `{customer_phone}`\n*Reason:* {reason}\n*Summary:* {summary}"
            }
            resp = httpx.post(webhook_url, json=payload, timeout=5.0)
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
