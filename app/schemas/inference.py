from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class BookingSlotData(BaseModel):
    customer_name: Optional[str] = Field(None, description="Full name of customer if mentioned")
    customer_phone: Optional[str] = Field(None, description="Phone number formatted in E.164 or local format")
    customer_email: Optional[str] = Field(None, description="Valid email address")
    service_name: Optional[str] = Field(None, description="Specific service or treatment requested")
    preferred_date: Optional[str] = Field(None, description="Requested date in YYYY-MM-DD")
    preferred_time: Optional[str] = Field(None, description="Requested time in HH:MM (24h format)")
    notes: Optional[str] = Field(None, description="Special requests or instructions")

    class Config:
        extra = "ignore"


class AgentInferenceOutput(BaseModel):
    detected_language: str = Field(
        default="english", description="Detected language and script style of the user"
    )
    detected_intent: str = Field(
        default="inquiry", description="Primary classification of user intent"
    )
    extracted_slots: BookingSlotData = Field(
        default_factory=BookingSlotData,
        description="Any booking slots explicitly identified in the user message"
    )
    requires_human_escalation: bool = Field(
        False, description="True if customer is angry, frustrated, or explicitly demands a human"
    )
    escalation_reason: Optional[str] = Field(None, description="Brief explanation if escalated")
    confidence_score: float = Field(default=0.95, description="Confidence between 0.0 and 1.0")
    assistant_reply: str = Field(
        ..., description="Final natural response in the user style, under 80 words with 1 clear CTA"
    )

    class Config:
        extra = "ignore"

