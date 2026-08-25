import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=List[schemas.BookingOut])
def list_bookings(
    channel: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    q = db.query(models.Booking).filter(
        (models.Booking.tenant_id == tenant.id) | (models.Booking.tenant_id == "default")
    )
    if channel:
        q = q.filter(models.Booking.channel == channel)
    bookings = q.order_by(models.Booking.created_at.desc()).all()

    demo_leads = db.query(models.DemoBooking).filter(
        (models.DemoBooking.tenant_id == tenant.id) | (models.DemoBooking.tenant_id == "default")
    ).order_by(models.DemoBooking.created_at.desc()).all()

    existing_ids = {b.id for b in bookings}
    res = list(bookings)
    for dl in demo_leads:
        if dl.id in existing_ids:
            continue
        res.append(
            models.Booking(
                id=dl.id,
                tenant_id=tenant.id,
                channel=dl.whatsapp_account_id or "whatsapp",
                customer_name=dl.name or "Demo Lead",
                name=dl.name or "Demo Lead",
                customer_email=dl.email,
                customer_phone=dl.phone_number,
                contact=dl.phone_number,
                service_name=dl.service_needed or "AI Automation Demo",
                notes=f"Industry: {dl.industry or 'N/A'} | Service: {dl.service_needed or 'N/A'}",
                status=dl.status or "pending",
                created_at=dl.created_at
            )
        )
    return sorted(res, key=lambda x: x.created_at or datetime.datetime.min, reverse=True)

