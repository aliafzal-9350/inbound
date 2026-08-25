import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from ..core.database import Base

try:
    from pgvector.sqlalchemy import Vector
    VectorType = Vector(1536)
except Exception:
    from sqlalchemy import JSON
    VectorType = JSON


def gen_id():
    return str(uuid.uuid4())


class TenantKnowledgeChunk(Base):
    __tablename__ = "tenant_knowledge_chunks"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="general")
    chunk_title = Column(String(200), nullable=True)
    chunk_content = Column(Text, nullable=False)
    embedding = Column(VectorType, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_chunks")


# Backward compatible KnowledgeEntry
class KnowledgeEntry(Base):
    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_entries")
