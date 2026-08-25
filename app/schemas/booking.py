import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SlotAvailabilityRequest(BaseModel):
    date: str  # YYYY-MM-DD
    timezone: str = "Asia/Karachi"
    service_id: Optional[str] = None


class TimeSlot(BaseModel):
    start_time: str  # ISO-8601 or HH:MM
    end_time: str    # ISO-8601 or HH:MM
    available: bool = True


class SlotAvailabilityResponse(BaseModel):
    date: str
    available_slots: List[str]


class BookingCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    service_name: str
    booking_start_time: datetime.datetime
    booking_end_time: Optional[datetime.datetime] = None
    notes: Optional[str] = None


class BookingOut(BaseModel):
    id: str
    channel: Optional[str] = "whatsapp"
    conversation_id: Optional[str] = None
    name: Optional[str] = None
    contact: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    service_name: Optional[str] = None
    booking_start_time: Optional[datetime.datetime] = None
    booking_end_time: Optional[datetime.datetime] = None
    calendar_event_id: Optional[str] = None
    status: Optional[str] = "confirmed"
    created_at: datetime.datetime

    class Config:
        from_attributes = True
