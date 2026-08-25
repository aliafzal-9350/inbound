import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base


def gen_id():
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=gen_id)
    business_name = Column(String(255), nullable=False, default="Default Business")
    name = Column(String(255), nullable=True)  # Backward compat alias
    slug = Column(String(100), unique=True, nullable=False, default=lambda: f"tenant-{uuid.uuid4().hex[:8]}")
    api_key = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    is_active = Column(Boolean, default=True)
    
    # Target Architecture fields
    default_timezone = Column(String(50), default="Asia/Karachi")
    calendar_provider = Column(String(30), default="cal_com")
    calendar_api_key_encrypted = Column(Text, nullable=True)
    calendar_event_type_id = Column(String(100), nullable=True)
    system_prompt_override = Column(Text, nullable=True)
    custom_system_prompt = Column(Text, nullable=True)  # Backward compat alias

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    knowledge_entries = relationship("KnowledgeEntry", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_chunks = relationship("TenantKnowledgeChunk", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tenant", cascade="all, delete-orphan")
    connections = relationship("ChannelConnection", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "name" in kwargs and "business_name" not in kwargs:
            kwargs["business_name"] = kwargs["name"]
        elif "business_name" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs["business_name"]
        if "custom_system_prompt" in kwargs and "system_prompt_override" not in kwargs:
            kwargs["system_prompt_override"] = kwargs["custom_system_prompt"]
        elif "system_prompt_override" in kwargs and "custom_system_prompt" not in kwargs:
            kwargs["custom_system_prompt"] = kwargs["system_prompt_override"]
        super().__init__(**kwargs)

    @property
    def display_name(self) -> str:
        return self.business_name or self.name or "Business"

    @property
    def timezone(self) -> str:
        return self.default_timezone or "Asia/Karachi"



class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class ChannelConnection(Base):
    __tablename__ = "channel_connections"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    channel = Column(String(20), nullable=False)  # whatsapp, instagram, facebook
    connection_method = Column(String(20), nullable=False, default="official_api")
    external_account_id = Column(String(255), nullable=True)  # phone_number_id, page_id, ig_account_id
    access_token = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    extra = Column(JSON, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="connections")
