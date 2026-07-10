from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "SafeSpace API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://safespace:safespace@postgres:5432/safespace"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Vector DB
    QDRANT_URL: str = "http://qdrant:6333"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    # Sync DB URL for Celery workers (psycopg2, not asyncpg — Celery tasks run outside the
    # async event loop, so they use a plain sync SQLAlchemy session).
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://safespace:safespace@postgres:5432/safespace"

    # Auth / JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # LLM provider
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-5"
    LLM_MAX_TOKENS: int = 1024

    # DL model-serving microservice (see ml-service/)
    ML_SERVICE_URL: str = "http://ml-service:8100"

    # Voice (STT/TTS) — see app/ai/voice_adapter.py
    OPENAI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
