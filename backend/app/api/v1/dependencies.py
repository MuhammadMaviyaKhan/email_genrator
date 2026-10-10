from fastapi import Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
import jwt
import hashlib
import secrets

from app.db.database import get_db
from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedError, SessionExpiredError, SessionInvalidError,
    RateLimitError, NotFoundError
)
from app.models.models import Session, EmailAddress, RateLimit


security = HTTPBearer(auto_error=False)
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )
    return redis_client


async def get_current_session(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Session:
    if not credentials:
        raise UnauthorizedError("Missing authorization header")
    
    token = credentials.credentials
    
    result = await db.execute(
        select(Session).where(
            Session.token == token,
            Session.is_active == True,
            Session.expires_at > datetime.utcnow(),
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise SessionExpiredError()
    
    session.last_activity_at = datetime.utcnow()
    await db.commit()
    
    return session


async def get_current_email_address(
    session: Session = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> EmailAddress:
    result = await db.execute(
        select(EmailAddress).where(
            EmailAddress.id == session.email_address_id,
            EmailAddress.status == "active",
        )
    )
    email_address = result.scalar_one_or_none()
    
    if not email_address:
        raise NotFoundError("Email address not found or inactive")
    
    if email_address.expires_at < datetime.utcnow():
        email_address.status = "expired"
        await db.commit()
        raise SessionExpiredError()
    
    return email_address


class RateLimiter:
    def __init__(self):
        self.local_cache: dict = {}
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int]:
        try:
            redis_client = await get_redis()
            await redis_client.ping()
        except Exception:
            return self._check_local_rate_limit(identifier, endpoint, limit, window)

        key = f"ratelimit:{identifier}:{endpoint}"
        current = await redis_client.get(key)

        if current is None:
            await redis_client.setex(key, window, 1)
            return True, window

        count = int(current)
        if count >= limit:
            ttl = await redis_client.ttl(key)
            return False, max(ttl, 1)

        await redis_client.incr(key)
        ttl = await redis_client.ttl(key)
        return True, max(ttl, 1)

    def _check_local_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int]:
        import time
        now = time.time()
        key = f"{identifier}:{endpoint}"
        entry = self.local_cache.get(key)
        if entry is None or entry[1] < now:
            self.local_cache[key] = (1, now + window)
            return True, window
        count, expires = entry
        if count >= limit:
            return False, max(int(expires - now), 1)
        self.local_cache[key] = (count + 1, expires)
        return True, max(int(expires - now), 1)
    
    async def check_email_generation_limit(
        self,
        identifier: str,
    ) -> Tuple[bool, int]:
        return await self.check_rate_limit(
            identifier=identifier,
            endpoint="generate_email",
            limit=settings.RATE_LIMIT_GENERATE_EMAIL,
            window=settings.RATE_LIMIT_GENERATE_WINDOW,
        )


async def verify_admin_token(
    x_admin_token: Optional[str] = Header(None),
) -> bool:
    if not x_admin_token:
        raise UnauthorizedError("Admin token required")
    
    expected_token = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    if not secrets.compare_digest(x_admin_token, expected_token):
        raise UnauthorizedError("Invalid admin token")
    
    return True


async def get_optional_session(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[Session]:
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        result = await db.execute(
            select(Session).where(
                Session.token == token,
                Session.is_active == True,
                Session.expires_at > datetime.utcnow(),
            )
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


async def get_optional_email_address(
    session: Optional[Session] = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
) -> Optional[EmailAddress]:
    if not session:
        return None
    
    result = await db.execute(
        select(EmailAddress).where(
            EmailAddress.id == session.email_address_id,
            EmailAddress.status == "active",
        )
    )
    return result.scalar_one_or_none()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return secrets.compare_digest(hash_password(plain), hashed)


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)