import datetime
from typing import Optional, List
from pydantic import BaseModel

from .inference import BookingSlotData, AgentInferenceOutput
from .webhook import (
    WhatsAppWebhookPayload,
    WhatsAppEntry,
    WhatsAppChange,
    WhatsAppValue,
    WhatsAppMessageItem,
    MetaWebhookPayload,
    MetaEntry,
    MetaMessagingEvent,
)
from .booking import (
    SlotAvailabilityRequest,
    SlotAvailabilityResponse,
    BookingCreate,
    BookingOut,
    TimeSlot,
)


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantOut(BaseModel):
    id: str
    name: Optional[str] = None
    business_name: Optional[str] = None
    slug: str
    api_key: str

    class Config:
        from_attributes = True


class TenantBasic(BaseModel):
    id: str
    name: Optional[str] = None
    business_name: Optional[str] = None
    slug: str

    class Config:
        from_attributes = True


class SignupIn(BaseModel):
    business_name: str
    slug: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


class ResetPasswordIn(BaseModel):
    email: str
    new_password: str


class AuthOut(BaseModel):
    token: str
    tenant: TenantBasic
    email: str


class MeOut(BaseModel):
    tenant: TenantBasic
    email: str


class KnowledgeCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "general"


class KnowledgeOut(BaseModel):
    id: str
    question: str
    answer: str
    is_active: bool

    class Config:
        from_attributes = True


class TestMessageIn(BaseModel):
    channel: str
    contact_external_id: str
    contact_name: Optional[str] = None
    message: str


class BookingInfo(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    preferred_time: Optional[str] = None
    notes: Optional[str] = None


class TestMessageOut(BaseModel):
    reply: str
    booking_created: bool
    booking_info: Optional[BookingInfo] = None
    detected_language: Optional[str] = None
    detected_intent: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    direction: str
    body: str
    media_url: Optional[str] = None
    audio_transcript: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    channel: str
    contact_external_id: str
    contact_name: Optional[str] = None
    customer_phone_or_id: Optional[str] = None
    customer_name: Optional[str] = None
    language_preference: Optional[str] = "roman_urdu"
    fsm_state: Optional[str] = "IDLE"
    is_escalated: Optional[bool] = False
    last_message_at: datetime.datetime

    class Config:
        from_attributes = True


class WhatsAppOfficialConnectIn(BaseModel):
    phone_number_id: str
    access_token: str
    waba_id: Optional[str] = None


class ChannelConnectionOut(BaseModel):
    id: str
    channel: str
    connection_method: str
    external_account_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class WhatsAppQrStatusOut(BaseModel):
    status: str
    qr: Optional[str] = None


class WhatsAppQrStatusWebhookIn(BaseModel):
    tenant_id: str
    status: str


class WhatsAppQrMessageIn(BaseModel):
    tenant_id: str
    sender: str
    name: Optional[str] = None
    text: str


class FacebookConnectIn(BaseModel):
    page_id: str
    access_token: str


class InstagramConnectIn(BaseModel):
    ig_business_account_id: str
    access_token: str


__all__ = [
    "BookingSlotData",
    "AgentInferenceOutput",
    "WhatsAppWebhookPayload",
    "WhatsAppEntry",
    "WhatsAppChange",
    "WhatsAppValue",
    "WhatsAppMessageItem",
    "MetaWebhookPayload",
    "MetaEntry",
    "MetaMessagingEvent",
    "SlotAvailabilityRequest",
    "SlotAvailabilityResponse",
    "BookingCreate",
    "BookingOut",
    "TimeSlot",
    "TenantCreate",
    "TenantOut",
    "TenantBasic",
    "SignupIn",
    "LoginIn",
    "ResetPasswordIn",
    "AuthOut",
    "MeOut",
    "KnowledgeCreate",
    "KnowledgeOut",
    "TestMessageIn",
    "BookingInfo",
    "TestMessageOut",
    "MessageOut",
    "ConversationOut",
    "WhatsAppOfficialConnectIn",
    "ChannelConnectionOut",
    "WhatsAppQrStatusOut",
    "WhatsAppQrStatusWebhookIn",
    "WhatsAppQrMessageIn",
    "FacebookConnectIn",
    "InstagramConnectIn",
]
