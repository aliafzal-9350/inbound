import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Enterprise AI Response & Autonomous Booking Engine"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = Field(default="production", alias="ENVIRONMENT")
    
    # Host & Memory Limits (AWS EC2 8GB budget)
    MAX_CONTAINER_MEMORY_MB: int = 3200
    
    # Database (PostgreSQL + pgvector)
    DATABASE_URL: str = Field(
        default="postgresql://postgres:secure_pass@localhost:5432/ai_agent_db",
        alias="DATABASE_URL"
    )
    
    # Redis (Locks, Debounce, 5-min holds)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    REDIS_DEBOUNCE_WINDOW_SECONDS: float = 1.8
    REDIS_MUTEX_LOCK_TTL_SECONDS: int = 8
    REDIS_SLOT_HOLD_TTL_SECONDS: int = 300  # 5 minutes
    
    # LLM & AI Providers
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    GROQ_API_KEY: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    GROQ_WHISPER_MODEL: str = Field(default="whisper-large-v3", alias="GROQ_WHISPER_MODEL")
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    XAI_API_KEY: Optional[str] = Field(default=None, alias="XAI_API_KEY")
    XAI_MODEL: str = Field(default="grok-3-mini", alias="XAI_MODEL")

    # Semantic RAG Configuration
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.25, alias="RAG_SIMILARITY_THRESHOLD")
    RAG_TOP_K: int = Field(default=4, alias="RAG_TOP_K")
    RAG_MAX_CONTEXT_CHUNKS: int = Field(default=5, alias="RAG_MAX_CONTEXT_CHUNKS")
    RAG_FALLBACK_MESSAGE: str = Field(
        default="I don't have enough information in the available company knowledge to answer that accurately.",
        alias="RAG_FALLBACK_MESSAGE"
    )
    RAG_DEBUG_LOGGING: bool = Field(default=True, alias="RAG_DEBUG_LOGGING")

    
    # Cal.com & Google Calendar
    CALCOM_API_KEY: Optional[str] = Field(default=None, alias="CALCOM_API_KEY")
    CALCOM_API_BASE: str = Field(default="https://api.cal.com/v2", alias="CALCOM_API_BASE")
    CALCOM_EVENT_TYPE_ID: Optional[str] = Field(default=None, alias="CALCOM_EVENT_TYPE_ID")
    GOOGLE_CALENDAR_CREDENTIALS_JSON: Optional[str] = Field(default=None, alias="GOOGLE_CALENDAR_CREDENTIALS_JSON")
    
    # Meta / WhatsApp / Instagram / Messenger
    META_APP_SECRET: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    META_WEBHOOK_VERIFY_TOKEN: str = Field(default="ravisn-dev-verify-token", alias="META_WEBHOOK_VERIFY_TOKEN")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = Field(default="ravisn-dev-verify-token", alias="WHATSAPP_WEBHOOK_VERIFY_TOKEN")
    WHATSAPP_QR_SERVICE_URL: str = Field(default="http://127.0.0.1:3001", alias="WHATSAPP_QR_SERVICE_URL")
    WHATSAPP_QR_INTERNAL_SECRET: str = Field(default="dev-internal-secret", alias="WHATSAPP_QR_INTERNAL_SECRET")
    
    # Security
    JWT_SECRET: str = Field(default="360808ff90807bb71369711ab46cb97f2bf947ccfd3069ee9fcb2844819383a0", alias="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24 * 7
    
    # Staff / Escalation Webhook
    STAFF_ESCALATION_WEBHOOK_URL: Optional[str] = Field(default=None, alias="STAFF_ESCALATION_WEBHOOK_URL")
    STAFF_WHATSAPP_NUMBER: Optional[str] = Field(default=None, alias="STAFF_WHATSAPP_NUMBER")
    
    # CORS
    CORS_ORIGINS: str = Field(default="*", alias="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
