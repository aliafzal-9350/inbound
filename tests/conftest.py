"""Test isolation: point the app at a throwaway SQLite database and in-memory Redis fallback
BEFORE any app module is imported, so tests never touch production data."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_db_path = os.path.join(tempfile.mkdtemp(prefix="ravisn-tests-"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"   # nothing listens there -> in-memory fallback
os.environ["JWT_SECRET"] = "test-only-jwt-secret-not-for-production-use"
os.environ["STAFF_ESCALATION_WEBHOOK_URL"] = "https://platform-owner.example/alerts"
