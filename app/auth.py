from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import jwt as pyjwt

from . import crud, models
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


def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    """Jwt auth. Used by the dashboard after a human logs in."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_current_tenant_flexible(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Accepts either a logged-in user's jwt, a tenant api key, or defaults to the master company tenant."""
    if authorization is not None:
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
        return user.tenant

    if x_api_key is not None:
        tenant = crud.get_tenant_by_api_key(db, x_api_key)
        if not tenant:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if not tenant.is_active:
            raise HTTPException(status_code=403, detail="Tenant is inactive")
        return tenant

    # Auto-fallback for master company tenant (RAVISN UK) when no auth headers are provided
    tenant = db.query(models.Tenant).filter(models.Tenant.slug == "ravisn-uk").first()
    if not tenant:
        tenant = crud.create_tenant(db, "RAVISN UK", "ravisn-uk")
    return tenant
