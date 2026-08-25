import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import schemas, models, pipeline, crud
from ..database import get_db
from ..auth import get_current_tenant_flexible
from ..services.meta_gateway import MetaGateway
from ..core.security import verify_meta_signature

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whatsapp-official"])

WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
APP_SECRET = os.getenv("META_APP_SECRET", "")


@router.post("/whatsapp/official/connect", response_model=schemas.ChannelConnectionOut)
def connect_official(
    payload: schemas.WhatsAppOfficialConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    extra = {"waba_id": payload.waba_id} if payload.waba_id else None
    return crud.upsert_channel_connection(
        db, tenant.id, "whatsapp", "official_api", payload.phone_number_id, payload.access_token, extra
    )


@router.get("/webhooks/whatsapp")
def verify_webhook(request: Request):
    verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    app_secret = os.getenv("META_APP_SECRET", "").strip()

    signature = request.headers.get("x-hub-signature-256", "")
    if app_secret and signature:
        if not verify_meta_signature(raw_body, signature, app_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body or b"{}")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages")
            if not messages:
                continue

            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            connection = db.query(models.ChannelConnection).filter(
                models.ChannelConnection.channel == "whatsapp",
                models.ChannelConnection.connection_method == "official_api",
                models.ChannelConnection.external_account_id == phone_number_id,
            ).first()
            if not connection:
                continue

            contacts = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}

            for msg in messages:
                msg_type = msg.get("type")
                sender = msg["from"]
                contact_name = contacts.get(sender)
                text = ""
                audio_bytes = None
                mime_type = None

                if msg_type == "text":
                    text = msg.get("text", {}).get("body", "")
                elif msg_type in ("audio", "voice"):
                    audio_obj = msg.get("audio") or msg.get("voice") or {}
                    media_id = audio_obj.get("id")
                    mime_type = audio_obj.get("mime_type", "audio/ogg")
                    if media_id:
                        media_url = await MetaGateway.fetch_meta_media_url(media_id, connection.access_token)
                        if media_url:
                            try:
                                from ..services.audio_processor import AudioProcessor
                                audio_bytes = await AudioProcessor.download_media(media_url, connection.access_token)
                            except Exception as e:
                                logger.error(f"Failed to download WhatsApp voice note: {e}")
                else:
                    continue

                # Run through the pipeline
                result = await pipeline.process_incoming_message_async(
                    db=db,
                    tenant=connection.tenant,
                    channel="whatsapp",
                    contact_external_id=sender,
                    contact_name=contact_name,
                    message_text=text,
                    audio_bytes=audio_bytes,
                    mime_type=mime_type
                )

                await MetaGateway.send_whatsapp_message(
                    phone_number_id=connection.external_account_id,
                    access_token=connection.access_token,
                    to_phone=sender,
                    message_text=result["reply"]
                )

    return {"status": "ok"}
