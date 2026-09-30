import asyncio
import logging
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session, joinedload

from . import crud, models
from .core.config import settings
from .core.redis import RedisService, conversation_turn_lock
from .services import sales_agent
from .services.audio_processor import AudioProcessor
from .services.llm_engine import LinguisticNormalizer

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = (".ogg", ".opus", ".m4a", ".mp3", ".wav")


def process_incoming_message(
    db: Session,
    tenant: models.Tenant,
    channel: str,
    contact_external_id: str,
    contact_name: Optional[str],
    message_text: str,
    media_url: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    debounce: bool = True,
) -> Dict[str, Any]:
    """Synchronous entry point wrapping process_incoming_message_async."""
    coro = process_incoming_message_async(
        db, tenant, channel, contact_external_id, contact_name,
        message_text, media_url, audio_bytes, mime_type, debounce,
    )
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


def _result(convo: Optional[models.Conversation], reply: Optional[str], turn=None) -> Dict[str, Any]:
    booking = getattr(turn, "booking", None)
    return {
        "conversation": convo,
        "reply": reply,  # None = nothing to send (message folded into a newer one in the same burst)
        "booking_created": bool(turn and turn.booking_created),
        "booking_info": {
            "name": booking.customer_name,
            "contact": booking.contact,
            "preferred_time": booking.preferred_time,
            "notes": booking.notes,
        } if booking else None,
        "detected_language": turn.language if turn else None,
        "detected_intent": ",".join(turn.intents) if turn else None,
        "fsm_state": convo.fsm_state if convo else None,
        "is_escalated": bool(turn and turn.escalated),
        "degraded": bool(turn and turn.degraded),
    }


async def process_incoming_message_async(
    db: Session,
    tenant: models.Tenant,
    channel: str,
    contact_external_id: str,
    contact_name: Optional[str],
    message_text: str,
    media_url: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    debounce: bool = True,
) -> Dict[str, Any]:
    """Saves the inbound message, waits briefly so rapid-fire messages are answered together,
    then lets the sales agent handle all unanswered messages as one turn."""
    tenant_id = str(tenant.id)
    text = LinguisticNormalizer.clean_text(message_text or "")
    # The database can be a continent away (~250ms per round trip). Don't let every commit expire and
    # re-fetch the tenant/conversation; the turn reloads fresh state explicitly once it holds the lock.
    db.expire_on_commit = False

    audio_transcript = None
    if audio_bytes or (media_url and media_url.lower().endswith(AUDIO_EXTENSIONS)):
        try:
            if not audio_bytes and media_url:
                audio_bytes = await AudioProcessor.download_media(media_url)
            if audio_bytes:
                transcript, _confidence, _needs_recovery = await AudioProcessor.process_voice_note(
                    audio_bytes, mime_type or "audio/ogg")
                audio_transcript = transcript
                if transcript:
                    text = f"{text} {transcript}".strip()
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")

    convo = crud.get_or_create_conversation(db, tenant_id, channel, contact_external_id, contact_name)
    if not text:
        text = "[voice note - could not be transcribed]" if audio_bytes else "[unsupported message]"
    crud.save_message(db, convo.id, "inbound", text, media_url=media_url, audio_transcript=audio_transcript,
                      convo=convo)

    burst_key = f"{tenant_id}:{channel}:{contact_external_id}"
    if debounce:
        ticket = RedisService.bump_counter(burst_key)
        await asyncio.sleep(settings.REDIS_DEBOUNCE_WINDOW_SECONDS)
        if RedisService.get_counter(burst_key) != ticket:
            return _result(convo, None)  # a newer message in this burst will answer everything

    async with conversation_turn_lock(burst_key):
        # one query: fresh conversation + all its messages (picks up writes from concurrent requests)
        convo = (db.query(models.Conversation).options(joinedload(models.Conversation.messages))
                 .populate_existing().filter(models.Conversation.id == convo.id).one())
        messages: List[models.Message] = list(convo.messages)
        last_id = (convo.agent_state or {}).get("last_inbound_id")
        index = next((i for i, m in enumerate(messages) if m.id == last_id), -1)
        pending = [m for m in messages[index + 1:] if m.direction == "inbound"]
        if not pending:
            return _result(convo, None)  # already answered by a concurrent request

        pending_ids = {m.id for m in pending}
        history = [{"role": "user" if m.direction == "inbound" else "assistant", "content": m.body}
                   for m in messages if m.id not in pending_ids]
        combined = "\n".join(m.body for m in pending)

        try:
            turn = await sales_agent.handle_turn(db, tenant, convo, channel, combined, history, contact_name)
            reply = turn.reply
        except Exception:
            logger.exception("[Pipeline] agent turn failed")
            db.rollback()
            turn = None
            reply = "Sorry, I ran into a problem on my side. Could you send that again?"

        # the agent leaves its state changes pending; they're saved in the same commit as the reply
        state = dict(convo.agent_state or {})
        state["last_inbound_id"] = pending[-1].id
        convo.agent_state = state
        crud.save_message(db, convo.id, "outbound", reply, convo=convo)
        return _result(convo, reply, turn)
