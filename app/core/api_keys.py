"""API keys that can be rotated at runtime from the dashboard (Settings -> API keys).

A key saved there is stored in Redis, so every worker process picks it up within
_CACHE_SECONDS and it survives restarts. The value in .env is the fallback.
"""
import os
import time
from typing import Dict, Optional, Tuple

from .config import settings
from .redis import RedisService

_CACHE_SECONDS = 30
_cache: Dict[str, Tuple[float, Optional[str]]] = {}


def get_key(name: str) -> Optional[str]:
    cached = _cache.get(name)
    if cached and cached[0] > time.time():
        return cached[1]
    saved = RedisService.get_config(name)
    if saved is not None:          # set from the dashboard; "" means explicitly removed there
        value = saved.strip() or None
    else:
        value = (getattr(settings, name, None) or os.getenv(name) or "").strip() or None
    _cache[name] = (time.time() + _CACHE_SECONDS, value)
    return value


def set_key(name: str, value: Optional[str]) -> None:
    """Saves (or with None removes) a runtime key; takes effect in all workers within 30s.
    A removal is stored as "" so it also overrides the value Docker passed in from .env."""
    RedisService.set_config(name, value or "")
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
    _cache.pop(name, None)
