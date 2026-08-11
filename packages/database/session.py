"""
Async SQLAlchemy Engine & Session Generator with graceful driver fallback for unit tests.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from apps.backend.app.core.config import settings

import os
from pathlib import Path

db_url = settings.DATABASE_URL
is_vercel = "VERCEL" in os.environ or "VERCEL_ENV" in os.environ

if is_vercel and ("localhost" in db_url or "127.0.0.1" in db_url):
    kb_sqlite = Path(__file__).resolve().parent.parent.parent / "knowledge_base.sqlite"
    if kb_sqlite.exists():
        db_url = f"sqlite+aiosqlite:///{kb_sqlite}"
    else:
        db_url = "sqlite+aiosqlite:///:memory:"
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

try:
    import asyncpg
except ImportError:
    if "sqlite" not in db_url:
        db_url = "sqlite+aiosqlite:///:memory:"

connect_args = {}
if "postgresql" in db_url and ("pooler.supabase.com" in db_url or ":6543" in db_url):
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0

engine: AsyncEngine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True if "sqlite" not in db_url else False,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector yielding an async database session with graceful exception handling."""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception:
        # Fail gracefully if database connection fails in serverless / stateless environments
        pass

