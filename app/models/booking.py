import uuid
import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


def gen_id():
    return str(uuid.uuid4())


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(20), nullable=True, default="whatsapp")
    
    # Target Architecture relational fields
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_email = Column(String(100), nullable=True)
    service_name = Column(String(100), nullable=True)
    booking_start_time = Column(DateTime, nullable=True)
    booking_end_time = Column(DateTime, nullable=True)
    calendar_event_id = Column(String(150), nullable=True)
    status = Column(String(30), default="confirmed")
    
    # Backward compatibility fields
    name = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)
    preferred_time = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="bookings")

    def __init__(self, **kwargs):
        if "customer_name" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs["customer_name"]
        elif "name" in kwargs and "customer_name" not in kwargs:
            kwargs["customer_name"] = kwargs["name"]
        if "customer_phone" in kwargs and "contact" not in kwargs:
            kwargs["contact"] = kwargs["customer_phone"]
        elif "contact" in kwargs and "customer_phone" not in kwargs:
            kwargs["customer_phone"] = kwargs["contact"]
        super().__init__(**kwargs)


class DemoBooking(Base):
    __tablename__ = "demo_bookings"

    id = Column(String(36), primary_key=True, default=gen_id)
    tenant_id = Column(String(64), nullable=False, index=True)
    whatsapp_account_id = Column(String(64), nullable=True)
    phone_number = Column(String(32), nullable=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    service_needed = Column(Text, nullable=True)
    raw_conversation = Column(Text, nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

