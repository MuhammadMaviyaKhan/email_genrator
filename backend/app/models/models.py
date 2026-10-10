from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import JSON as SQLJSON
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
import enum
from datetime import datetime
from typing import Optional, List

from app.db.database import Base, _is_sqlite
from app.core.config import settings


USE_PG = not _is_sqlite(settings.DATABASE_URL)

if USE_PG:
    UUIDType = UUIDType
    JSONType = JSONType
else:
    UUIDType = String(36)
    JSONType = SQLJSON


class EmailStatus(str, enum.Enum):
    RECEIVED = "received"
    READ = "read"
    DELETED = "deleted"
    EXPIRED = "expired"
    FAILED = "failed"


class EmailAddressStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    DELETED = "deleted"


class EmailAddress(Base):
    __tablename__ = "email_addresses"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    local_part = Column(String(100), nullable=False, index=True)
    domain = Column(String(100), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    status = Column(SQLEnum(EmailAddressStatus, values_callable=lambda e: [m.value for m in e]), default=EmailAddressStatus.ACTIVE, 
nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    emails_count = Column(Integer, default=0, nullable=False)
    max_emails = Column(Integer, default=100, nullable=False)
    is_custom = Column(Boolean, default=False, nullable=False)
    token = Column(String(255), unique=True, nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    emails = relationship("Email", back_populates="email_address", cascade="all, delete-orphan", lazy="dynamic")
    sessions = relationship("Session", back_populates="email_address", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_email_addresses_email_status", "email", "status"),
        Index("ix_email_addresses_expires_status", "expires_at", "status"),
    )
    
    def __repr__(self):
        return f"<EmailAddress(email='{self.email}', status='{self.status}')>"


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_address_id = Column(UUIDType, ForeignKey("email_addresses.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    from_address = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    to_addresses = Column(JSONType, nullable=True)
    cc_addresses = Column(JSONType, nullable=True)
    bcc_addresses = Column(JSONType, nullable=True)
    reply_to = Column(String(255), nullable=True)
    text_body = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    raw_source = Column(Text, nullable=True)
    headers = Column(JSONType, nullable=True)
    attachments = Column(JSONType, nullable=True)
    status = Column(SQLEnum(EmailStatus, values_callable=lambda e: [m.value for m in e]), default=EmailStatus.RECEIVED, nullable=False, 
index=True)
    size_bytes = Column(Integer, default=0, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    spam_score = Column(Integer, nullable=True)
    is_spam = Column(Boolean, default=False, nullable=False)
    
    email_address = relationship("EmailAddress", back_populates="emails")
    
    __table_args__ = (
        Index("ix_emails_address_status_received", "email_address_id", "status", "received_at"),
        Index("ix_emails_message_id_address", "message_id", "email_address_id", unique=True),
    )
    
    def __repr__(self):
        return f"<Email(id='{self.id}', subject='{self.subject}', from='{self.from_address}')>"


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = Column(UUIDType, ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(Integer, default=0, nullable=False)
    content_id = Column(String(255), nullable=True)
    is_inline = Column(Boolean, default=False, nullable=False)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Attachment(filename='{self.filename}', content_type='{self.content_type}')>"


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_address_id = Column(UUIDType, ForeignKey("email_addresses.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    email_address = relationship("EmailAddress", back_populates="sessions")
    
    __table_args__ = (
        Index("ix_sessions_token_active", "token", "is_active"),
    )
    
    def __repr__(self):
        return f"<Session(token='{self.token[:10]}...', email_id='{self.email_address_id}')>"


class Domain(Base):
    __tablename__ = "domains"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    mx_record = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    emails_received = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f"<Domain(domain='{self.domain}', active={self.is_active})>"


class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    identifier = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    count = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_rate_limits_identifier_endpoint_window", "identifier", "endpoint", "window_end"),
    )
    
    def __repr__(self):
        return f"<RateLimit(identifier='{self.identifier}', endpoint='{self.endpoint}', count={self.count})>"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUIDType, primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(20), nullable=True, index=True)
    message = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True, index=True)
    user_id = Column(UUIDType, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index("ix_audit_logs_entity_created", "entity_type", "entity_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<AuditLog(event='{self.event_type}', entity='{self.entity_type}')>"
