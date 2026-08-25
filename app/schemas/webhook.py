from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WhatsAppProfile(BaseModel):
    name: Optional[str] = None


class WhatsAppContact(BaseModel):
    profile: Optional[WhatsAppProfile] = None
    wa_id: str


class WhatsAppTextMessage(BaseModel):
    body: str


class WhatsAppAudioMessage(BaseModel):
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None


class WhatsAppMessageItem(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str  # text, audio, voice, interactive, etc.
    text: Optional[WhatsAppTextMessage] = None
    audio: Optional[WhatsAppAudioMessage] = None
    voice: Optional[WhatsAppAudioMessage] = None


class WhatsAppMetadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: str


class WhatsAppValue(BaseModel):
    messaging_product: str = "whatsapp"
    metadata: WhatsAppMetadata
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessageItem]] = None


class WhatsAppChange(BaseModel):
    field: str
    value: WhatsAppValue


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]


# Instagram & Facebook Messenger Schemas
class MetaSender(BaseModel):
    id: str


class MetaRecipient(BaseModel):
    id: str


class MetaMessageBody(BaseModel):
    mid: Optional[str] = None
    text: Optional[str] = None
    is_echo: Optional[bool] = False
    attachments: Optional[List[Dict[str, Any]]] = None


class MetaMessagingEvent(BaseModel):
    sender: MetaSender
    recipient: MetaRecipient
    timestamp: Optional[int] = None
    message: Optional[MetaMessageBody] = None


class MetaEntry(BaseModel):
    id: str
    time: Optional[int] = None
    messaging: Optional[List[MetaMessagingEvent]] = None


class MetaWebhookPayload(BaseModel):
    object: str  # 'page' or 'instagram'
    entry: List[MetaEntry]
