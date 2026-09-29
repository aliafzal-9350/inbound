"""Regression test: a Meta webhook message delivered twice must only be processed once,
but a delivery whose processing failed must stay retryable."""
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.redis import claim_webhook_event, RedisService


def test_second_delivery_is_skipped():
    mid = f"m_test_{uuid.uuid4().hex}"
    with claim_webhook_event(mid) as first:
        assert first is True
        with claim_webhook_event(mid) as concurrent:
            assert concurrent is False  # same message arriving while the first is processing
    with claim_webhook_event(mid) as retry:
        assert retry is False  # Meta retry after a successful reply
    RedisService.release_lock(f"webhook_event:{mid}")


def test_failed_processing_releases_claim():
    mid = f"m_test_{uuid.uuid4().hex}"
    try:
        with claim_webhook_event(mid):
            raise RuntimeError("LLM provider down")
    except RuntimeError:
        pass
    with claim_webhook_event(mid) as retry:
        assert retry is True  # Meta's retry gets a chance to succeed
    RedisService.release_lock(f"webhook_event:{mid}")


def test_missing_event_id_is_always_processed():
    with claim_webhook_event(None) as first:
        assert first is True
    with claim_webhook_event(None) as again:
        assert again is True
