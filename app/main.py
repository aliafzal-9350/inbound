from dotenv import load_dotenv
load_dotenv()  # must run before any app module reads os.getenv() at import time

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .core.database import Base, engine, DATABASE_URL, get_db, init_db_extensions
from .core.config import settings
from .core.redis import RedisService
from .routers import (
    tenants, knowledge, chat, auth, conversations,
    whatsapp_official, whatsapp_qr, meta_messaging,
    bookings, settings as settings_router, channels, public_legal
)

# Auto-create tables for local sqlite dev or synchronize columns on PostgreSQL
try:
    init_db_extensions(engine)
except Exception as e:
    print(f"[Init Warning] DB extension initialization: {e}")

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[Init Warning] DB table auto-creation: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: attempt pgvector / extensions and table initialization
    try:
        init_db_extensions(engine)
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Startup Warning] DB extension/table initialization: {e}")
    yield
    # Shutdown


app = FastAPI(
    title="Enterprise AI Response & Autonomous Booking Engine",
    description="Stateful, voice-aware, trilingual (English, Roman Urdu, Nastaliq Urdu) AI booking platform.",
    version="2.0.0",
    lifespan=lifespan
)

CORS_ORIGINS = settings.CORS_ORIGINS
origins = ["*"] if CORS_ORIGINS == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:8000"] if origins == ["*"] else origins,
    allow_origin_regex=r".*" if origins == ["*"] else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

all_routers = [
    auth.router, tenants.router, knowledge.router, chat.router,
    conversations.router, whatsapp_official.router, whatsapp_qr.router,
    meta_messaging.router, bookings.router, settings_router.router,
    channels.router, public_legal.router
]

for router in all_routers:
    app.include_router(router)

# Mount all routers under /api prefix for Vercel / serverless routing
api_router = APIRouter(prefix="/api")
for router in all_routers:
    api_router.include_router(router)


@api_router.get("/")
def api_root():
    return {
        "status": "ok",
        "service": "enterprise-ai-booking-engine",
        "redis_connected": RedisService.is_available(),
    }


@api_router.get("/health")
def api_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "redis": RedisService.is_available()
    }


app.include_router(api_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "enterprise-ai-booking-engine",
        "redis_connected": RedisService.is_available(),
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "redis": RedisService.is_available()
    }
