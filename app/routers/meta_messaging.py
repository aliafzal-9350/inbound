import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import schemas, models, pipeline, crud
from ..database import get_db
from ..auth import get_current_tenant_flexible
from ..integrations import meta_messaging
from ..security import verify_meta_signature

router = APIRouter(tags=["meta-messaging"])

WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
APP_SECRET = os.getenv("META_APP_SECRET", "")
MOCK_MODE = not bool(APP_SECRET)


@router.post("/facebook/connect", response_model=schemas.ChannelConnectionOut)
def connect_facebook(
    payload: schemas.FacebookConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    """Manual connect for now (paste page_id + page access token from the Meta app
    dashboard). Until RAVISN's app has completed App Review for pages_messaging,
    this only works for pages where you've added yourself as an admin/tester on
    the app."""
    return crud.upsert_channel_connection(
        db, tenant.id, "facebook", "official_api", payload.page_id, payload.access_token
    )


@router.post("/instagram/connect", response_model=schemas.ChannelConnectionOut)
def connect_instagram(
    payload: schemas.InstagramConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    """Manual connect (paste the instagram business account id + access token).
    Same App Review caveat as facebook applies here."""
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
    """Handles both facebook messenger and instagram dms - meta sends them through
    the same payload shape, just with a different top-level 'object' value."""
    raw_body = await request.body()
    app_secret = os.getenv("META_APP_SECRET", "").strip()

    # if app_secret:
        # signature = request.headers.get("x-hub-signature-256", "")
        # if not verify_meta_signature(raw_body, signature, app_secret):
            # raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body or b"{}")
    object_type = payload.get("object")
    if object_type not in ("page", "instagram"):
        return {"status": "ignored"}

    channel = "facebook" if object_type == "page" else "instagram"

    for entry in payload.get("entry", []):
        account_id = entry.get("id")
        connection = db.query(models.ChannelConnection).filter(
            models.ChannelConnection.channel == channel,
            models.ChannelConnection.connection_method == "official_api",
            models.ChannelConnection.external_account_id == account_id,
        ).first()
        if not connection:
            continue  # message for a page/account we don't have on file, ignore

        for event in entry.get("messaging", []):
            message = event.get("message")
            if not message or message.get("is_echo"):
                continue  # skip our own sent messages and non-message events for now
            text = message.get("text")
            if not text:
                continue  # phase 4 handles text only; attachments/postbacks come later
            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                continue

            # Send typing_on indicator immediately so customer sees "Agent is typing..."
            meta_messaging.send_typing_indicator(connection.access_token, sender_id)

            result = pipeline.process_incoming_message(db, connection.tenant, channel, sender_id, None, text)

            if channel == "facebook":
                meta_messaging.send_facebook_message(connection.access_token, sender_id, result["reply"])
            else:
                meta_messaging.send_instagram_message(
                    connection.external_account_id, connection.access_token, sender_id, result["reply"]
                )

    return {"status": "ok"}
