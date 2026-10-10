import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_, func

from app.db.database import get_db, async_session_maker
from app.models.models import (
    EmailAddress, Email, Session, AuditLog, RateLimit
)
from app.core.config import settings
from app.core.logging.logging import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}
        self.running = False
    
    async def start(self):
        self.running = True
        self.tasks["cleanup_expired"] = asyncio.create_task(self._cleanup_loop())
        self.tasks["rate_limit_cleanup"] = asyncio.create_task(self._rate_limit_cleanup_loop())
        self.tasks["session_cleanup"] = asyncio.create_task(self._session_cleanup_loop())
        logger.info("Task scheduler started")
    
    async def stop(self):
        self.running = False
        for task in self.tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("Task scheduler stopped")
    
    async def _cleanup_loop(self):
        while self.running:
            try:
                await self.cleanup_expired_addresses()
                await self.cleanup_expired_emails()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _rate_limit_cleanup_loop(self):
        while self.running:
            try:
                await self.cleanup_rate_limits()
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
                await asyncio.sleep(300)
    
    async def _session_cleanup_loop(self):
        while self.running:
            try:
                await self.cleanup_expired_sessions()
                await asyncio.sleep(120)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(120)
    
    async def cleanup_expired_addresses(self):
        async with async_session_maker() as db:
            now = datetime.utcnow()
            result = await db.execute(
                select(EmailAddress).where(
                    EmailAddress.expires_at < now,
                    EmailAddress.status == "active",
                )
            )
            expired = result.scalars().all()
            
            for addr in expired:
                addr.status = "expired"
                addr.updated_at = now
            
            await db.commit()
            
            if expired:
                logger.info(f"Marked {len(expired)} addresses as expired")
    
    async def cleanup_expired_emails(self):
        async with async_session_maker() as db:
            cutoff = datetime.utcnow() - timedelta(days=settings.EMAIL_RETENTION_DAYS)
            result = await db.execute(
                delete(Email).where(
                    Email.received_at < cutoff,
                    Email.status.in_(["read", "deleted"]),
                )
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Deleted {result.rowcount} old emails")
    
    async def cleanup_expired_sessions(self):
        async with async_session_maker() as db:
            now = datetime.utcnow()
            result = await db.execute(
                delete(Session).where(
                    or_(Session.expires_at < now, Session.is_active == False)
                )
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Deleted {result.rowcount} expired sessions")
    
    async def cleanup_rate_limits(self):
        async with async_session_maker() as db:
            now = datetime.utcnow()
            result = await db.execute(
                delete(RateLimit).where(RateLimit.window_end < now)
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} rate limit records")


scheduler = TaskScheduler()


async def start_background_tasks():
    await scheduler.start()


async def stop_background_tasks():
    await scheduler.stop()