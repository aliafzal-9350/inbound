import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from ..schemas.inference import BookingSlotData
from ..core.redis import RedisService

logger = logging.getLogger(__name__)


class BookingState(str, Enum):
    IDLE = "IDLE"
    COLLECTING_SERVICE = "COLLECTING_SERVICE"
    COLLECTING_NAME = "COLLECTING_NAME"
    COLLECTING_PHONE = "COLLECTING_PHONE"
    COLLECTING_EMAIL = "COLLECTING_EMAIL"
    COLLECTING_DATETIME = "COLLECTING_DATETIME"
    CHECKING_CALENDAR = "CHECKING_CALENDAR"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class BookingStateMachine:
    REQUIRED_SLOTS = ["service_name", "customer_name", "customer_phone", "preferred_date", "preferred_time"]

    @classmethod
    def get_current_slots(cls, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Fetches accumulated slot data from Redis session cache."""
        return RedisService.get_session_state(tenant_id, user_id)

    @classmethod
    def save_slots(cls, tenant_id: str, user_id: str, slots: Dict[str, Any]) -> None:
        """Saves slot data dictionary to Redis session cache."""
        RedisService.set_session_state(tenant_id, user_id, slots or {})


    @classmethod
    def merge_and_save_slots(
        cls,
        tenant_id: str,
        user_id: str,
        current_slots: Dict[str, Any],
        new_slots: BookingSlotData
    ) -> Dict[str, Any]:
        """Progressively accumulates new slots on top of existing session slots."""
        merged = dict(current_slots or {})
        for field, val in new_slots.model_dump().items():
            if val is not None and str(val).strip():
                merged[field] = val

        RedisService.set_session_state(tenant_id, user_id, merged)
        return merged


    @classmethod
    def determine_next_state(
        cls,
        current_state: str,
        accumulated_slots: Dict[str, Any],
        intent: str,
        is_escalated: bool = False
    ) -> str:
        """Deterministically calculates next state in the state machine graph."""
        if is_escalated:
            return BookingState.ESCALATED.value

        if intent == "cancel":
            return BookingState.CANCELLED.value

        # If user is not engaged in booking and no slots captured, stay IDLE
        if intent not in ("booking_request", "reschedule") and not accumulated_slots:
            return BookingState.IDLE.value

        # Check required fields in order
        if not accumulated_slots.get("service_name"):
            return BookingState.COLLECTING_SERVICE.value
        if not accumulated_slots.get("customer_name"):
            return BookingState.COLLECTING_NAME.value
        if not accumulated_slots.get("customer_phone"):
            return BookingState.COLLECTING_PHONE.value
        if not (accumulated_slots.get("preferred_date") and accumulated_slots.get("preferred_time")):
            return BookingState.COLLECTING_DATETIME.value

        # If all slots are present, transition to checking calendar or awaiting confirmation
        if current_state == BookingState.AWAITING_CONFIRMATION.value and intent in ("greeting", "inquiry", "general_inquiry"):
            # User confirmed or acknowledged
            return BookingState.CONFIRMED.value

        return BookingState.AWAITING_CONFIRMATION.value

    @classmethod
    def reset_session(cls, tenant_id: str, user_id: str) -> None:
        """Clears slot memory upon booking completion or cancellation."""
        RedisService.set_session_state(tenant_id, user_id, {})
