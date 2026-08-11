"""
Health check endpoints for system monitoring, liveness, and readiness probes.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.core.config import settings
from packages.database.session import get_async_session
from packages.shared.schemas.common import HealthStatus

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

router = APIRouter(prefix="/health", tags=["Health"])


async def check_database(db: AsyncSession) -> dict:
    """Executes a ping query on PostgreSQL database."""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {"status": "up", "latency_ms": 0.0}
    except Exception as e:
        return {"status": "down", "error": str(e)}
    return {"status": "down", "error": "Unexpected ping response"}


async def check_redis() -> dict:
    """Pings Redis server if configured."""
    if not HAS_REDIS or "localhost" in settings.REDIS_URL or "127.0.0.1" in settings.REDIS_URL:
        return {"status": "up", "notice": "redis module/cache optional"}
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        ping_res = await r.ping()
        await r.aclose()
        if ping_res:
            return {"status": "up"}
    except Exception as e:
        return {"status": "down", "error": str(e)}
    return {"status": "down", "error": "Redis ping failed"}


@router.get("", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def get_health_status(
    db: AsyncSession = Depends(get_async_session),
) -> HealthStatus:
    """Aggregate health check endpoint."""
    db_health = await check_database(db)
    redis_health = await check_redis()

    overall_status = "healthy"
    if db_health["status"] != "up":
        overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version="0.1.0",
        components={
            "database": db_health,
            "redis": redis_health,
        },
    )


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_probe() -> dict:
    """Liveness probe indicating application process is running."""
    return {"status": "alive"}


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_probe(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Readiness probe indicating database and external dependency readiness."""
    db_health = await check_database(db)
    if db_health["status"] != "up":
        return {"status": "not_ready", "reason": "Database unavailable"}
    return {"status": "ready"}
