import jwt
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.config import settings


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def decode_token_unverified(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return secrets.compare_digest(hash_password(plain_password), hashed_password)


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_otp(length: int = 6) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_api_key() -> str:
    return f"tm_{secrets.token_urlsafe(32)}"


def constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a, b)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def sanitize_string(value: str, max_length: int = 255) -> str:
    if not value:
        return ""
    return value.strip()[:max_length]


def validate_email_format(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_csp_nonce() -> str:
    return secrets.token_urlsafe(16)