from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class EmailStatus(str, Enum):
    RECEIVED = "received"
    READ = "read"
    DELETED = "deleted"
    EXPIRED = "expired"
    FAILED = "failed"


class EmailAddressStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    DELETED = "deleted"


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    content_type: str
    size: int
    content_id: Optional[str] = None
    is_inline: bool
    download_url: Optional[str] = None


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email_address_id: UUID
    message_id: str
    subject: Optional[str] = None
    from_address: str
    from_name: Optional[str] = None
    to_addresses: Optional[List[str]] = None
    cc_addresses: Optional[List[str]] = None
    bcc_addresses: Optional[List[str]] = None
    reply_to: Optional[str] = None
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    raw_source: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    attachments: Optional[List[AttachmentResponse]] = None
    status: EmailStatus
    size_bytes: int
    received_at: datetime
    read_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    spam_score: Optional[int] = None
    is_spam: bool = False


class EmailDetail(EmailResponse):
    otp_codes: List[Dict[str, Any]] = []
    verification_links: List[Dict[str, Any]] = []


class EmailList(BaseModel):
    emails: List[EmailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmailAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    local_part: str
    domain: str
    status: EmailAddressStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    emails_count: int
    max_emails: int
    is_custom: bool
    deleted_at: Optional[datetime] = None
    token: Optional[str] = None


class EmailAddressList(BaseModel):
    items: List[EmailAddressResponse]
    total: int
    page: int
    per_page: int
    pages: int


class EmailAddressCreate(BaseModel):
    local_part: Optional[str] = Field(None, min_length=1, max_length=64)
    domain: Optional[str] = None
    password: Optional[str] = Field(None, min_length=4, max_length=128)
    ttl_hours: Optional[int] = Field(None, ge=1, le=168)
    max_emails: Optional[int] = Field(None, ge=1, le=1000)


class EmailAddressUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=4, max_length=128)
    max_emails: Optional[int] = Field(None, ge=1, le=1000)
    ttl_hours: Optional[int] = Field(None, ge=1, le=168)


class GenerateEmailRequest(BaseModel):
    count: int = Field(1, ge=1, le=10)
    domain: Optional[str] = None
    ttl_hours: Optional[int] = Field(None, ge=1, le=168)
    prefix: Optional[str] = Field(None, max_length=32)
    password_protected: bool = False
    max_emails: Optional[int] = Field(None, ge=1, le=1000)


class GenerateEmailResponse(BaseModel):
    email: EmailAddressResponse
    token: str
    password: Optional[str] = None
    expires_at: datetime
    addresses: Optional[List[EmailAddressResponse]] = None


class CustomEmailRequest(BaseModel):
    local_part: str = Field(..., min_length=1, max_length=64)
    domain: str = Field(..., min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=4, max_length=128)
    max_emails: Optional[int] = Field(None, ge=1, le=1000)


class CustomEmailResponse(BaseModel):
    email: EmailAddressResponse
    token: str
    expires_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    email: EmailAddressResponse
    session_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    email: Optional[EmailAddressResponse] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email_address_id: UUID
    token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_active: bool


class SessionList(BaseModel):
    sessions: List[SessionResponse]
    total: int


class DeleteResponse(BaseModel):
    message: str
    id: Optional[str] = None


class StatsResponse(BaseModel):
    total_emails: int = 0
    emails_today: int = 0
    emails_this_week: int = 0
    emails_this_month: int = 0
    max_emails: int = 100
    remaining_emails: int = 100
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    email: Optional[EmailAddressResponse] = None
    total_addresses: int = 0
    active_addresses: int = 0
    expired_addresses: int = 0
    active_domains: int = 0
    total_domains: int = 0


class OTPCode(BaseModel):
    code: str
    length: int
    source: str = "regex"
    context: Optional[str] = None


class VerificationLink(BaseModel):
    url: str
    text: str
    type: str = "verification"


class OTPExtractionResponse(BaseModel):
    email_id: UUID
    subject: Optional[str] = None
    from_address: str
    otp_codes: List[OTPCode]
    verification_links: List[VerificationLink]
    extracted_at: datetime


class EmailSourceResponse(BaseModel):
    raw_source: str


class OTPResponse(BaseModel):
    email_id: str
    otp_codes: List[Dict[str, Any]]
    primary_otp: Optional[str] = None
    count: int = 0


class VerificationLinkResponse(BaseModel):
    email_id: str
    links: List[Dict[str, Any]]
    count: int = 0


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    domain: str
    is_active: bool
    is_default: bool
    mx_record: Optional[str] = None
    verification_token: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str
    smtp: str
    uptime_seconds: float
    websocket_connections: int = 0
    active_addresses: int = 0


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class EmailWSMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class WebSocketEvent(BaseModel):
    type: str
    email_id: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class EmailFilterParams(PaginationParams):
    status: Optional[EmailStatus] = None
    is_spam: Optional[bool] = None
    from_address: Optional[str] = None
    subject_contains: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class RateLimitResponse(BaseModel):
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None