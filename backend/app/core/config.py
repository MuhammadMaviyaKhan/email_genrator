import secrets
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    APP_NAME: str = "TempMail Pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    API_V1_PREFIX: str = "/api/v1"
    ADMIN_PREFIX: str = "/api/admin"
    
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tempmail"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 2525
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = False
    SMTP_TIMEOUT: int = 30
    
    DEFAULT_DOMAINS: List[str] = ["tempmail.pro", "tmpmail.io", "mailtemp.org"]
    DEFAULT_TTL_HOURS: int = 24
    MAX_TTL_HOURS: int = 168
    MIN_TTL_HOURS: int = 1
    DEFAULT_MAX_EMAILS: int = 100
    MAX_EMAILS_PER_ADDRESS: int = 1000
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_GENERATE_EMAIL: int = 10
    RATE_LIMIT_GENERATE_WINDOW: int = 60
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    ADMIN_EMAIL: str = "admin@tempmail.local"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    EMAIL_MAX_SIZE: int = 25 * 1024 * 1024
    EMAIL_RETENTION_DAYS: int = 7
    MAX_ATTACHMENT_SIZE: int = 10 * 1024 * 1024
    ALLOWED_ATTACHMENT_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "text/csv",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    
    SPAM_CHECK_ENABLED: bool = True
    SPAM_THRESHOLD: float = 5.0
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    SENTRY_DSN: Optional[str] = None
    
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    
    EMAIL_CHECK_INTERVAL: int = 2
    MAX_INBOX_SIZE: int = 1000
    
    OTP_PATTERNS: List[str] = [
        r'\b\d{4}\b',
        r'\b\d{5}\b',
        r'\b\d{6}\b',
        r'\b\d{8}\b',
        r'\b[A-Z0-9]{6,8}\b',
    ]
    
    VERIFICATION_LINK_PATTERNS: List[str] = [
        r'https?://[^\s]*(?:verify|confirm|activate|validate)[^\s]*',
        r'https?://[^\s]*(?:email|account|registration)[^\s]*',
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("DEFAULT_DOMAINS", mode="before")
    @classmethod
    def parse_domains(cls, v):
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(",")]
        return v

    @field_validator("ALLOWED_ATTACHMENT_TYPES", mode="before")
    @classmethod
    def parse_attachment_types(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()