import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base


def gen_id():
    return str(uuid.uuid4())


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "contact_external_id", name="uq_tenant_channel_contact"),
    )

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # whatsapp, instagram, facebook
    contact_external_id = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    
    # Target Architecture fields
    customer_phone_or_id = Column(String(255), nullable=True)
    customer_name = Column(String(255), nullable=True)
    language_preference = Column(String(20), default="roman_urdu")  # roman_urdu, urdu_nastaliq, english
    fsm_state = Column(String(50), default="IDLE")
    is_escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    
    last_message_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at"
    )

    def __init__(self, **kwargs):
        if "customer_phone_or_id" in kwargs and "contact_external_id" not in kwargs:
            kwargs["contact_external_id"] = kwargs["customer_phone_or_id"]
        elif "contact_external_id" in kwargs and "customer_phone_or_id" not in kwargs:
            kwargs["customer_phone_or_id"] = kwargs["contact_external_id"]
        if "customer_name" in kwargs and "contact_name" not in kwargs:
            kwargs["contact_name"] = kwargs["customer_name"]
        elif "contact_name" in kwargs and "customer_name" not in kwargs:
            kwargs["customer_name"] = kwargs["contact_name"]
        super().__init__(**kwargs)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_id)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    body = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    audio_transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
