"""
Sync SQLAlchemy engine/session for Celery workers. Celery tasks run outside FastAPI's async
event loop, so mixing in the asyncpg-based async engine would require bridging asyncio into
each worker process — a plain sync session (psycopg2) is simpler and battle-tested for this.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)


def get_sync_db() -> Session:
    return SyncSessionLocal()
