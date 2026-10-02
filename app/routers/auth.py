import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..auth import get_current_user, is_platform_admin, require_platform_admin
from ..core.redis import RedisService

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LENGTH = 8
MAX_FAILED_LOGINS = 10            # per email, per window
FAILED_LOGIN_WINDOW = 15 * 60     # seconds


def _auth_out(user: models.User) -> schemas.AuthOut:
    return schemas.AuthOut(token=create_access_token(user.id, user.tenant_id), tenant=user.tenant,
                           email=user.email, is_platform_admin=is_platform_admin(user))


def _check_new_password(password: str) -> None:
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")


@router.post("/signup", response_model=schemas.AuthOut)
def signup(payload: schemas.SignupIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    _check_new_password(payload.password)
    if db.query(models.User).filter(models.User.email == email).first():
        # Never log someone into an existing account from the signup form
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please log in.")

    raw_slug = re.sub(r"[^a-z0-9-]+", "-", (payload.slug or "").strip().lower()).strip("-") or "my-workspace"
    business_name = payload.business_name.strip() if payload.business_name else "My Business"

    # Auto-generate unique workspace URL slug if taken
    slug = raw_slug
    counter = 1
    while db.query(models.Tenant).filter(models.Tenant.slug == slug).first():
        slug = f"{raw_slug}-{counter}"
        counter += 1

    tenant = crud.create_tenant(db, business_name, slug)
    user = crud.create_user(db, tenant.id, email, hash_password(payload.password))
    return _auth_out(user)


@router.post("/login", response_model=schemas.AuthOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    throttle_key = f"failed_login:{email}"
    if RedisService.get_counter(throttle_key) >= MAX_FAILED_LOGINS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please try again in 15 minutes.")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        RedisService.bump_counter(throttle_key, ttl_seconds=FAILED_LOGIN_WINDOW)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.tenant or not user.tenant.is_active:
        raise HTTPException(status_code=403, detail="This workspace is inactive")
    return _auth_out(user)


@router.post("/change-password")
def change_password(payload: schemas.ChangePasswordIn, user: models.User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    _check_new_password(payload.new_password)
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok", "message": "Password changed."}


@router.post("/admin/reset-password")
def admin_reset_password(payload: schemas.AdminResetPasswordIn, _owner: models.User = Depends(require_platform_admin),
                         db: Session = Depends(get_db)):
    """Platform owner sets a temporary password for a client who forgot theirs."""
    target = db.query(models.User).filter(models.User.email == payload.email.strip().lower()).first()
    if not target:
        raise HTTPException(status_code=404, detail="No account found with this email address")
    _check_new_password(payload.new_password)
    target.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok", "message": f"Password for {target.email} has been reset."}


@router.get("/me", response_model=schemas.MeOut)
def me(user: models.User = Depends(get_current_user)):
    return schemas.MeOut(tenant=user.tenant, email=user.email, is_platform_admin=is_platform_admin(user))
