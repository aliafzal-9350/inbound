from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models, pipeline
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/test-message", response_model=schemas.TestMessageOut)
def test_message(
    payload: schemas.TestMessageIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    result = pipeline.process_incoming_message(
        db, tenant, payload.channel, payload.contact_external_id, payload.contact_name, payload.message,
        debounce=False,
    )
    return schemas.TestMessageOut(
        reply=result["reply"] or "",
        booking_created=result["booking_created"],
        booking_info=result["booking_info"],
    )
