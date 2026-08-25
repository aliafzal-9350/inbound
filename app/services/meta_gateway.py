import os
import logging
from typing import Dict, Any, Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaGateway:
    @staticmethod
    def is_mock_mode() -> bool:
        return not bool(settings.META_APP_SECRET)

    @classmethod
    async def send_whatsapp_message(
        cls,
        phone_number_id: str,
        access_token: str,
        to_phone: str,
        message_text: str
    ) -> Dict[str, Any]:
        """Dispatches an outbound text message via WhatsApp Cloud API."""
        if cls.is_mock_mode() and (not access_token or access_token == "mock" or access_token.startswith("test")):
            logger.info(f"[MOCK] WhatsApp Cloud API -> to {to_phone}: {message_text}")
            return {"messages": [{"id": f"mock-wa-{to_phone}"}], "mock": True}

        url = f"{GRAPH_BASE}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message_text}
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as err:
            error_detail = getattr(err.response, "text", "") if hasattr(err, "response") and err.response else ""
            logger.error(f"[WhatsApp API Error] {err} | Detail: {error_detail}")
            return {"error": str(err), "detail": error_detail}

    @classmethod
    async def send_instagram_message(
        cls,
        ig_account_id: str,
        access_token: str,
        recipient_igsid: str,
        message_text: str
    ) -> Dict[str, Any]:
        """Dispatches an outbound text message via Instagram Direct Messages."""
        if cls.is_mock_mode() and (not access_token or access_token == "mock" or access_token.startswith("ig-token")):
            logger.info(f"[MOCK] Instagram DM -> to {recipient_igsid}: {message_text}")
            return {"mock": True}

        if access_token and access_token.startswith("IGAAM"):
            url = "https://graph.instagram.com/v20.0/me/messages"
        else:
            url = f"{GRAPH_BASE}/{ig_account_id}/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_igsid},
            "message": {"text": message_text}
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as err:
            error_detail = getattr(err.response, "text", "") if hasattr(err, "response") and err.response else ""
            logger.error(f"[Instagram API Error] {err} | Detail: {error_detail}")
            return {"error": str(err), "detail": error_detail}

    @classmethod
    async def send_facebook_message(
        cls,
        page_access_token: str,
        recipient_psid: str,
        message_text: str
    ) -> Dict[str, Any]:
        """Dispatches an outbound text message via Facebook Messenger."""
        if cls.is_mock_mode() and (not page_access_token or page_access_token == "mock" or page_access_token.startswith("fb-token")):
            logger.info(f"[MOCK] Facebook Messenger -> to {recipient_psid}: {message_text}")
            return {"mock": True}

        url = f"{GRAPH_BASE}/me/messages"
        params = {"access_token": page_access_token}
        payload = {
            "recipient": {"id": recipient_psid},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, params=params, json=payload)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as err:
            error_detail = getattr(err.response, "text", "") if hasattr(err, "response") and err.response else ""
            logger.error(f"[Facebook API Error] {err} | Detail: {error_detail}")
            return {"error": str(err), "detail": error_detail}

    @classmethod
    async def send_typing_indicator(cls, access_token: str, recipient_id: str) -> None:
        """Sends typing_on indicator to Meta platforms."""
        if cls.is_mock_mode() or not access_token or access_token == "mock" or access_token.startswith("test"):
            return

        if access_token.startswith("IGAAM"):
            url = "https://graph.instagram.com/v20.0/me/messages"
        else:
            url = f"{GRAPH_BASE}/me/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": "typing_on"
        }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(url, headers=headers, json=payload)
        except Exception as e:
            logger.debug(f"Typing indicator warning: {e}")

    @classmethod
    async def fetch_meta_media_url(cls, media_id: str, access_token: str) -> Optional[str]:
        """Queries Meta Graph API to retrieve the CDN direct download URL for an audio/media asset."""
        if not media_id or not access_token or access_token.startswith("test"):
            return None

        url = f"{GRAPH_BASE}/{media_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json().get("url")
        except Exception as e:
            logger.error(f"Failed to fetch Meta media URL: {e}")
        return None
