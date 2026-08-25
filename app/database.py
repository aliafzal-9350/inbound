# Backward-compatible re-export from core.database
from .core.database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    DATABASE_URL,
    init_db_extensions,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "DATABASE_URL",
    "init_db_extensions",
]
