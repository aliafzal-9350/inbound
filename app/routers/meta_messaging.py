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

router = APIRouter(tags=["meta-messaging"])

WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
APP_SECRET = os.getenv("META_APP_SECRET", "")


@router.post("/facebook/connect", response_model=schemas.ChannelConnectionOut)
def connect_facebook(
    payload: schemas.FacebookConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    return crud.upsert_channel_connection(
        db, tenant.id, "facebook", "official_api", payload.page_id, payload.access_token
    )


@router.post("/instagram/connect", response_model=schemas.ChannelConnectionOut)
def connect_instagram(
    payload: schemas.InstagramConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    return crud.upsert_channel_connection(
        db, tenant.id, "instagram", "official_api", payload.ig_business_account_id, payload.access_token
    )


@router.get("/webhooks/meta")
def verify_webhook(request: Request):
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/meta")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    app_secret = os.getenv("META_APP_SECRET", "").strip()

    signature = request.headers.get("x-hub-signature-256", "")
    if app_secret and signature:
        if not verify_meta_signature(raw_body, signature, app_secret):
            logger.warning("[Meta Webhook] Signature verification failed. Check META_APP_SECRET in .env.")
            if os.getenv("META_STRICT_SIGNATURE", "false").lower() == "true":
                raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body or b"{}")
    object_type = payload.get("object")
    if object_type not in ("page", "instagram"):
        return {"status": "ignored"}

    channel = "facebook" if object_type == "page" else "instagram"
    logger.info(f"[Meta Webhook] Received webhook object={object_type} for channel={channel}")

    for entry in payload.get("entry", []):
        account_id = entry.get("id")
        logger.info(f"[Meta Webhook] Processing entry id={account_id}")
        
        # 1. Primary lookup by channel and external_account_id
        connection = db.query(models.ChannelConnection).filter(
            models.ChannelConnection.channel == channel,
            models.ChannelConnection.connection_method == "official_api",
            models.ChannelConnection.external_account_id == account_id,
        ).first()
        
        # 2. Fallback: match by external_account_id across any channel (in case Instagram webhook came via page object)
        if not connection:
            connection = db.query(models.ChannelConnection).filter(
                models.ChannelConnection.external_account_id == account_id,
            ).first()

        # 3. Fallback: if single connection exists for the tenant, use it
        if not connection:
            connection = db.query(models.ChannelConnection).filter(
                models.ChannelConnection.channel.in_(["facebook", "instagram"]),
                models.ChannelConnection.status == "connected",
            ).first()

        if not connection:
            logger.warning(f"[Meta Webhook] No ChannelConnection found for account_id={account_id}. Active connections: {[c.external_account_id for c in db.query(models.ChannelConnection).all()]}")
            continue

        actual_channel = connection.channel

        for event in entry.get("messaging", []):
            message = event.get("message")
            if not message or message.get("is_echo"):
                continue
            text = message.get("text")
            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                continue

            attachments = message.get("attachments", [])
            audio_bytes = None
            mime_type = None

            if attachments:
                for att in attachments:
                    if att.get("type") == "audio":
                        audio_url = att.get("payload", {}).get("url")
                        if audio_url:
                            try:
                                from ..services.audio_processor import AudioProcessor
                                audio_bytes = await AudioProcessor.download_media(audio_url, connection.access_token)
                                mime_type = "audio/mp4"
                            except Exception as e:
                                logger.error(f"Failed to download audio attachment: {e}")

            if not text and not audio_bytes:
                continue

            # Send typing_on indicator
            await MetaGateway.send_typing_indicator(connection.access_token, sender_id)

            result = await pipeline.process_incoming_message_async(
                db=db,
                tenant=connection.tenant,
                channel=actual_channel,
                contact_external_id=sender_id,
                contact_name=None,
                message_text=text or "",
                audio_bytes=audio_bytes,
                mime_type=mime_type
            )

            if actual_channel == "facebook":
                await MetaGateway.send_facebook_message(connection.access_token, sender_id, result["reply"])
            else:
                await MetaGateway.send_instagram_message(
                    connection.external_account_id, connection.access_token, sender_id, result["reply"]
                )

    return {"status": "ok"}
