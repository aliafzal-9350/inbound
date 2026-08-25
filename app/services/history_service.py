from typing import Optional, List
from sqlalchemy.orm import Session
from .. import crud, models
from ..core.database import SessionLocal


def get_recent_chat_history_sync(db: Session, tenant_id: str, user_id: str, limit: int = 6) -> str:
    """Fetches the last N messages for a conversation and formats as a clean readable history string."""
    convo = db.query(models.Conversation).filter(
        models.Conversation.tenant_id == tenant_id,
        models.Conversation.external_user_id == user_id
    ).first()
    
    if not convo or not convo.messages:
        return "No prior conversation history."
        
    recent_msgs = convo.messages[-limit:]
    formatted_lines = []
    for msg in recent_msgs:
        role = "User" if msg.direction == "inbound" else "Assistant"
        formatted_lines.append(f"{role}: {msg.body}")
        
    return "\n".join(formatted_lines)


async def get_recent_chat_history(tenant_id: str, user_id: str, db: Optional[Session] = None, limit: int = 6) -> str:
    """Async wrapper fetching recent chat history turns."""
    local_db = db or SessionLocal()
    try:
        return get_recent_chat_history_sync(local_db, tenant_id, user_id, limit)
    finally:
        if db is None:
            local_db.close()
