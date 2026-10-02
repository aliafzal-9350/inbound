from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import jwt as pyjwt

from . import crud, models
from .core.config import settings
from .database import get_db
from .security import decode_access_token


def get_current_tenant(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    """Api-key auth. Kept for scripts/tests/future machine-to-machine use."""
    tenant = crud.get_tenant_by_api_key(db, x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")
    return tenant


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Jwt auth. Used by the dashboard after a human logs in."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.id == payload.get("user_id")).first()
    if not user or not user.tenant:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not user.tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")
    return user


def get_current_tenant_flexible(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Accepts either a logged-in user's jwt or a tenant api key. Anything else is rejected."""
    if authorization is not None:
        return get_current_user(authorization, db).tenant

    if x_api_key is not None:
        return get_current_tenant(x_api_key, db)

    raise HTTPException(status_code=401, detail="Not authenticated")


def is_platform_admin(user: Optional[models.User]) -> bool:
    admins = {e.strip().lower() for e in settings.PLATFORM_ADMIN_EMAILS.split(",") if e.strip()}
    return bool(user and user.email and user.email.strip().lower() in admins)


def require_platform_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Platform-wide settings (AI keys, workspace creation, password resets) are owner-only."""
    if not is_platform_admin(user):
        raise HTTPException(status_code=403, detail="Only the platform owner can do this")
    return user
