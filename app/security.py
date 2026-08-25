# Backward-compatible re-export from core.security
from .core.security import (
    verify_meta_signature,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRE_HOURS,
)

__all__ = [
    "verify_meta_signature",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_HOURS",
]
