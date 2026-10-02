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
    # Groq is the agent's only AI for thinking and writing. Each tier walks its own model list when a
    # model is rate-limited (Groq limits are per model). Writer = Qwen: in tests it was the only Groq model
    # that answers Roman Urdu in Latin letters (GPT-OSS switched to Hindi script).
    GROQ_API_KEY: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="qwen/qwen3.8-27b", alias="GROQ_MODEL")
    GROQ_SMART_FALLBACKS: str = Field(default="openai/gpt-oss-120b,openai/gpt-oss-20b", alias="GROQ_SMART_FALLBACKS")
    GROQ_FAST_MODEL: str = Field(default="openai/gpt-oss-120b", alias="GROQ_FAST_MODEL")
    GROQ_FAST_FALLBACKS: str = Field(default="qwen/qwen3.8-27b,openai/gpt-oss-20b", alias="GROQ_FAST_FALLBACKS")
    GROQ_WHISPER_MODEL: str = Field(default="whisper-large-v3", alias="GROQ_WHISPER_MODEL")
    # Gemini is used ONLY for knowledge-search embeddings (Groq has no embedding API); it never writes replies.
    GEMINI_API_KEY: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    GEMINI_EMBED_MODEL: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBED_MODEL")
    EMBEDDING_DIM: int = 1536  # must match the vector(1536) columns
    XAI_API_KEY: Optional[str] = Field(default=None, alias="XAI_API_KEY")
    XAI_MODEL: str = Field(default="grok-3-mini", alias="XAI_MODEL")

    # Semantic RAG Configuration
    # Floor on cosine similarity (gemini-embedding-001, normalized) for a knowledge entry to be shown to the reply
    # model as a candidate. Calibrated on the RAVISN FAQ: answerable questions score 0.61-0.81 but unrelated ones
    # reach ~0.70 against generic entries, so this only drops clear misses; the reply model judges the rest.
    RAG_MIN_DENSE_SCORE: float = Field(default=0.55, alias="RAG_MIN_DENSE_SCORE")
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
    # Platform owner(s): the only accounts that can see/change AI provider keys, create workspaces via the
    # API and reset other users' passwords. Comma-separated emails.
    PLATFORM_ADMIN_EMAILS: str = Field(default="ravisn.uk@gmail.com", alias="PLATFORM_ADMIN_EMAILS")
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
