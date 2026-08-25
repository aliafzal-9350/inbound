import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    if os.getenv("VERCEL"):
        DATABASE_URL = "sqlite:////tmp/ravisn_agent.db"
    else:
        DATABASE_URL = "sqlite:///./ravisn_agent.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite vs PostgreSQL configuration
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10 if not DATABASE_URL.startswith("sqlite") else 5,
    max_overflow=20 if not DATABASE_URL.startswith("sqlite") else 10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_extensions(db_engine=engine):
    """Enable pg extensions and ensure any missing columns exist on existing databases."""
    if not DATABASE_URL.startswith("sqlite"):
        with db_engine.connect() as conn:
            # 1. Extensions
            for ext in ["uuid-ossp", "vector", "pg_trgm"]:
                try:
                    conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}";'))
                    conn.commit()
                except Exception as e:
                    conn.rollback()

            # 2. Batch schema synchronization in a single round-trip
            batch_sql = """
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS business_name VARCHAR(255);
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS name VARCHAR(255);
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS default_timezone VARCHAR(50) DEFAULT 'Asia/Karachi';
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS calendar_provider VARCHAR(30) DEFAULT 'cal_com';
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS calendar_api_key_encrypted TEXT;
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS calendar_event_type_id VARCHAR(100);
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS system_prompt_override TEXT;
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS custom_system_prompt TEXT;

                CREATE TABLE IF NOT EXISTS tenant_knowledge_chunks (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    category VARCHAR(50) NOT NULL DEFAULT 'general',
                    chunk_title VARCHAR(200),
                    chunk_content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS customer_phone_or_id VARCHAR(255);
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255);
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS language_preference VARCHAR(20) DEFAULT 'roman_urdu';
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS fsm_state VARCHAR(50) DEFAULT 'IDLE';
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_escalated BOOLEAN DEFAULT FALSE;
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS escalation_reason TEXT;
                ALTER TABLE conversations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

                ALTER TABLE messages ADD COLUMN IF NOT EXISTS media_url VARCHAR(500);
                ALTER TABLE messages ADD COLUMN IF NOT EXISTS audio_transcript TEXT;

                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS customer_name VARCHAR(100);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(50);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS customer_email VARCHAR(100);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS service_name VARCHAR(100);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS booking_start_time TIMESTAMP WITH TIME ZONE;
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS booking_end_time TIMESTAMP WITH TIME ZONE;
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(150);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'confirmed';
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS name VARCHAR(255);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS contact VARCHAR(255);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS preferred_time VARCHAR(255);
                ALTER TABLE bookings ADD COLUMN IF NOT EXISTS notes TEXT;
            """
            try:
                conn.execute(text(batch_sql))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"[DB Schema Notice] {e}")

