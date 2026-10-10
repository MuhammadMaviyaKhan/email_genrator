from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from datetime import datetime, timedelta
import time
import psutil

from app.db.database import get_db
from app.core.config import settings
from app.schemas.schemas import HealthResponse
from app.models.models import EmailAddress

router = APIRouter()

start_time = time.time()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    async with db.begin():
        await db.execute(text("SELECT 1"))
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health(db: AsyncSession = Depends(get_db)):
    db_status = "healthy"
    redis_status = "not_configured"
    smtp_status = "unknown"
    
    try:
        async with db.begin():
            await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
    
    try:
        from app.api.v1.dependencies import get_redis
        redis = await get_redis()
        await redis.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unavailable"
    
    active_addresses = await db.scalar(
        select(func.count(EmailAddress.id)).where(
            EmailAddress.status == "active",
            EmailAddress.expires_at > datetime.utcnow(),
        )
    )
    
    uptime = time.time() - start_time
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        redis=redis_status,
        smtp=smtp_status,
        uptime_seconds=uptime,
        active_addresses=active_addresses or 0,
    )


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        async with db.begin():
            await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503


@router.get("/live")
async def liveness():
    return {"status": "alive", "uptime": time.time() - start_time}


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    process = psutil.Process()
    
    total_addresses = await db.scalar(select(func.count(EmailAddress.id)))
    active_addresses = await db.scalar(
        select(func.count(EmailAddress.id)).where(
            EmailAddress.status == "active",
            EmailAddress.expires_at > datetime.utcnow(),
        )
    )
    expired_addresses = await db.scalar(
        select(func.count(EmailAddress.id)).where(
            EmailAddress.status == "expired"
        )
    )
    
    return {
        "process": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "threads": process.num_threads(),
        },
        "addresses": {
            "total": total_addresses or 0,
            "active": active_addresses or 0,
            "expired": expired_addresses or 0,
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
    }