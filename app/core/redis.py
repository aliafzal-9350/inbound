import time
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager, contextmanager
from .config import settings

logger = logging.getLogger(__name__)

# Optional Redis connection with fallback to in-memory store
try:
    import redis
    _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_client.ping()
    _REDIS_AVAILABLE = True
except Exception as ex:
    logger.warning(f"Redis not reachable at {settings.REDIS_URL} ({ex}). Using in-memory fallback.")
    _redis_client = None
    _REDIS_AVAILABLE = False

# In-memory storage fallback
_in_memory_store: Dict[str, Any] = {}
_in_memory_expiry: Dict[str, float] = {}
_in_memory_locks: Dict[str, float] = {}


def _clean_expired_in_memory():
    now = time.time()
    expired_keys = [k for k, exp in _in_memory_expiry.items() if exp <= now]
    for k in expired_keys:
        _in_memory_store.pop(k, None)
        _in_memory_expiry.pop(k, None)
    expired_locks = [k for k, exp in _in_memory_locks.items() if exp <= now]
    for k in expired_locks:
        _in_memory_locks.pop(k, None)


class RedisService:
    @staticmethod
    def is_available() -> bool:
        return _REDIS_AVAILABLE

    @staticmethod
    def acquire_lock(lock_key: str, ttl_seconds: int = 8) -> bool:
        """Acquires a distributed mutex lock. Returns True if acquired, False otherwise."""
        if _REDIS_AVAILABLE and _redis_client:
            try:
                # SET key val NX EX ttl
                acquired = _redis_client.set(f"lock:{lock_key}", "locked", nx=True, ex=ttl_seconds)
                return bool(acquired)
            except Exception as e:
                logger.error(f"Redis acquire_lock failed: {e}")
        
        # In-memory fallback
        _clean_expired_in_memory()
        now = time.time()
        if lock_key in _in_memory_locks and _in_memory_locks[lock_key] > now:
            return False
        _in_memory_locks[lock_key] = now + ttl_seconds
        return True

    @staticmethod
    def release_lock(lock_key: str) -> None:
        """Releases the mutex lock."""
        if _REDIS_AVAILABLE and _redis_client:
            try:
                _redis_client.delete(f"lock:{lock_key}")
                return
            except Exception as e:
                logger.error(f"Redis release_lock failed: {e}")
        
        _in_memory_locks.pop(lock_key, None)

    @staticmethod
    def push_debounce_message(tenant_id: str, user_id: str, message: str) -> List[str]:
        """Appends message to the user debounce list with a sliding expiration window."""
        key = f"debounce:{tenant_id}:{user_id}"
        ttl = int(settings.REDIS_DEBOUNCE_WINDOW_SECONDS * 2)
        if _REDIS_AVAILABLE and _redis_client:
            try:
                pipe = _redis_client.pipeline()
                pipe.rpush(key, message)
                pipe.expire(key, ttl)
                pipe.lrange(key, 0, -1)
                results = pipe.execute()
                return results[2] if len(results) >= 3 else [message]
            except Exception as e:
                logger.error(f"Redis push_debounce_message failed: {e}")

        # In-memory fallback
        _clean_expired_in_memory()
        if key not in _in_memory_store:
            _in_memory_store[key] = []
        _in_memory_store[key].append(message)
        _in_memory_expiry[key] = time.time() + ttl
        return list(_in_memory_store[key])

    @staticmethod
    def clear_debounce_messages(tenant_id: str, user_id: str) -> None:
        key = f"debounce:{tenant_id}:{user_id}"
        if _REDIS_AVAILABLE and _redis_client:
            try:
                _redis_client.delete(key)
                return
            except Exception as e:
                logger.error(f"Redis clear_debounce failed: {e}")
        _in_memory_store.pop(key, None)
        _in_memory_expiry.pop(key, None)

    @staticmethod
    def set_slot_hold(tenant_id: str, slot_iso: str, user_id: str, ttl_seconds: int = 300) -> bool:
        """Holds a calendar slot for 5 minutes (300s) to prevent race conditions during booking confirmation."""
        key = f"hold:{tenant_id}:{slot_iso}"
        if _REDIS_AVAILABLE and _redis_client:
            try:
                acquired = _redis_client.set(key, user_id, nx=True, ex=ttl_seconds)
                return bool(acquired)
            except Exception as e:
                logger.error(f"Redis set_slot_hold failed: {e}")

        _clean_expired_in_memory()
        now = time.time()
        if key in _in_memory_store and _in_memory_expiry.get(key, 0) > now:
            if _in_memory_store[key] != user_id:
                return False
        _in_memory_store[key] = user_id
        _in_memory_expiry[key] = now + ttl_seconds
        return True

    @staticmethod
    def get_slot_hold(tenant_id: str, slot_iso: str) -> Optional[str]:
        key = f"hold:{tenant_id}:{slot_iso}"
        if _REDIS_AVAILABLE and _redis_client:
            try:
                return _redis_client.get(key)
            except Exception as e:
                logger.error(f"Redis get_slot_hold failed: {e}")

        _clean_expired_in_memory()
        return _in_memory_store.get(key)

    @staticmethod
    def release_slot_hold(tenant_id: str, slot_iso: str) -> None:
        key = f"hold:{tenant_id}:{slot_iso}"
        if _REDIS_AVAILABLE and _redis_client:
            try:
                _redis_client.delete(key)
                return
            except Exception as e:
                logger.error(f"Redis release_slot_hold failed: {e}")
        _in_memory_store.pop(key, None)
        _in_memory_expiry.pop(key, None)

    @staticmethod
    def set_session_state(tenant_id: str, user_id: str, state_dict: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Stores active conversation slot state in Redis."""
        key = f"session_state:{tenant_id}:{user_id}"
        val_str = json.dumps(state_dict)
        if _REDIS_AVAILABLE and _redis_client:
            try:
                _redis_client.set(key, val_str, ex=ttl_seconds)
                return
            except Exception as e:
                logger.error(f"Redis set_session_state failed: {e}")

        _clean_expired_in_memory()
        _in_memory_store[key] = val_str
        _in_memory_expiry[key] = time.time() + ttl_seconds

    @staticmethod
    def get_session_state(tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Loads active conversation slot state from Redis."""
        key = f"session_state:{tenant_id}:{user_id}"
        val_str = None
        if _REDIS_AVAILABLE and _redis_client:
            try:
                val_str = _redis_client.get(key)
            except Exception as e:
                logger.error(f"Redis get_session_state failed: {e}")

        if not val_str:
            _clean_expired_in_memory()
            val_str = _in_memory_store.get(key)

        if val_str:
            try:
                return json.loads(val_str)
            except Exception:
                pass
        return {}


@contextmanager
def session_lock(tenant_id: str, user_id: str, ttl: int = 8):
    """Context manager for acquiring and releasing a session mutex lock."""
    lock_key = f"tenant:{tenant_id}:user:{user_id}"
    acquired = RedisService.acquire_lock(lock_key, ttl_seconds=ttl)
    try:
        yield acquired
    finally:
        if acquired:
            RedisService.release_lock(lock_key)
