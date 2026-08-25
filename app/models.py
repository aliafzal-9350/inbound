# Backward-compatible re-export of all database models
from .models.tenant import Tenant, User, ChannelConnection, gen_id
from .models.knowledge import TenantKnowledgeChunk, KnowledgeEntry
from .models.conversation import Conversation, Message
from .models.booking import Booking

__all__ = [
    "Tenant",
    "User",
    "ChannelConnection",
    "TenantKnowledgeChunk",
    "KnowledgeEntry",
    "Conversation",
    "Message",
    "Booking",
    "gen_id",
]
