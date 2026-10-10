from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

from app.models.models import EmailAddress, Email, Session, Domain, Attachment
from app.core.exceptions import (
    NotFoundError, EmailAddressExpiredError, MaxEmailsReachedError
)
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.active_smtp_connections = {}
    
    async def create_email_address(
        self,
        db: AsyncSession,
        local_part: Optional[str] = None,
        domain: Optional[str] = None,
        password: Optional[str] = None,
        ttl_hours: Optional[int] = None,
        max_emails: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> EmailAddress:
        domain = domain or settings.DEFAULT_DOMAINS[0]
        
        result = await db.execute(select(Domain).where(Domain.domain == domain))
        domain_obj = result.scalar_one_or_none()
        
        if not domain_obj or not domain_obj.is_active:
            from app.core.exceptions import DomainNotAllowedError
            raise DomainNotAllowedError(domain, settings.DEFAULT_DOMAINS)
        
        if local_part:
            existing = await db.execute(
                select(EmailAddress).where(
                    EmailAddress.local_part == local_part,
                    EmailAddress.domain == domain,
                )
            )
            if existing.scalar_one_or_none():
                from app.core.exceptions import ConflictError
                raise ConflictError(f"Email {local_part}@{domain} already exists")
        else:
            local_part = await self._generate_unique_local_part(db, domain)
        
        ttl = ttl_hours or settings.DEFAULT_TTL_HOURS
        expires_at = datetime.utcnow() + timedelta(hours=ttl)
        
        password_hash = self.hash_password(password) if password else None
        
        email_address = EmailAddress(
            email=f"{local_part}@{domain}",
            local_part=local_part,
            domain=domain,
            password_hash=password_hash,
            status="active",
            expires_at=expires_at,
            max_emails=max_emails or settings.MAX_EMAILS_PER_ADDRESS,
            is_custom=bool(local_part),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.add(email_address)
        await db.flush()
        
        session = Session(
            email_address_id=email_address.id,
            token=self.generate_token(),
            expires_at=expires_at,
            is_active=True,
        )
        db.add(session)
        
        return email_address
    
    async def _generate_unique_local_part(self, db: AsyncSession, domain: str) -> str:
        import secrets
        import string
        while True:
            chars = string.ascii_lowercase + string.digits
            local_part = ''.join(secrets.choice(chars) for _ in range(10))
            existing = await db.execute(
                select(EmailAddress).where(
                    EmailAddress.local_part == local_part,
                    EmailAddress.domain == domain,
                    EmailAddress.status == "active",
                )
            )
            if not existing.scalar_one_or_none():
                return local_part
    
    async def receive_email(
        self,
        db: AsyncSession,
        to_address: str,
        from_address: str,
        subject: str,
        text_body: str,
        html_body: str,
        raw_source: str,
        attachments: Optional[List[Dict]] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[Email]:
        result = await db.execute(
            select(EmailAddress).where(
                EmailAddress.email == to_address,
                EmailAddress.status == "active",
            )
        )
        email_address = result.scalar_one_or_none()
        
        if not email_address:
            return None
        
        if email_address.expires_at < datetime.utcnow():
            email_address.status = "expired"
            await db.commit()
            return None
        
        total_emails = await db.scalar(
            select(func.count(Email.id)).where(Email.email_address_id == email_address.id)
        )
        
        if total_emails >= email_address.max_emails:
            raise MaxEmailsReachedError(email_address.email, email_address.max_emails)
        
        email = Email(
            email_address_id=email_address.id,
            message_id=str(uuid4()),
            subject=subject[:500] if subject else None,
            from_address=from_address[:255],
            text_body=text_body,
            html_body=html_body,
            raw_source=raw_source,
            headers=headers or {},
            status="received",
            size_bytes=len(raw_source.encode('utf-8')) if raw_source else 0,
            attachments=attachments or [],
            received_at=datetime.utcnow(),
        )
        
        db.add(email)
        
        email_address.emails_count = (email_address.emails_count or 0) + 1
        domain_result = await db.execute(select(Domain).where(Domain.domain == email_address.domain))
        domain_obj = domain_result.scalar_one_or_none()
        if domain_obj:
            domain_obj.emails_received = (domain_obj.emails_received or 0) + 1
        
        await db.commit()
        await db.refresh(email)
        
        return email
    
    async def get_inbox(
        self,
        db: AsyncSession,
        email_address_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = select(Email).where(Email.email_address_id == email_address_id)
        
        if status:
            query = query.where(Email.status == status)
        elif search:
            search_term = f"%{search}%"
            query = query.where(
                Email.subject.ilike(search_term) |
                Email.from_address.ilike(search_term) |
                Email.text_body.ilike(search_term)
            )
        
        query = query.order_by(Email.received_at.desc())
        
        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        emails = result.scalars().all()
        
        return {
            "emails": emails,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    
    async def get_email(
        self,
        db: AsyncSession,
        email_id: str,
        email_address_id: str,
    ) -> Optional[Email]:
        result = await db.execute(
            select(Email).where(
                Email.id == email_id,
                Email.email_address_id == email_address_id,
            )
        )
        email = result.scalar_one_or_none()
        
        if email and email.status == "received":
            email.status = "read"
            email.read_at = datetime.utcnow()
            await db.commit()
        
        return email
    
    async def delete_email(
        self,
        db: AsyncSession,
        email_id: str,
        email_address_id: str,
    ) -> bool:
        result = await db.execute(
            select(Email).where(
                Email.id == email_id,
                Email.email_address_id == email_address_id,
            )
        )
        email = result.scalar_one_or_none()
        
        if not email:
            return False
        
        email.status = "deleted"
        email.deleted_at = datetime.utcnow()
        await db.commit()
        return True
    
    async def delete_all_emails(
        self,
        db: AsyncSession,
        email_address_id: str,
    ) -> int:
        result = await db.execute(
            select(Email).where(
                Email.email_address_id == email_address_id,
                Email.status != "deleted",
            )
        )
        emails = result.scalars().all()
        
        for email in emails:
            email.status = "deleted"
            email.deleted_at = datetime.utcnow()
        
        await db.commit()
        return len(emails)
    
    async def extend_email(
        self,
        db: AsyncSession,
        email_address_id: str,
        hours: int,
    ) -> EmailAddress:
        result = await db.execute(
            select(EmailAddress).where(EmailAddress.id == email_address_id)
        )
        email_address = result.scalar_one_or_none()
        
        if not email_address:
            raise NotFoundError("Email address not found")
        
        if email_address.status != "active":
            raise EmailAddressExpiredError(email_address.email)
        
        email_address.expires_at = datetime.utcnow() + timedelta(hours=hours)
        email_address.updated_at = datetime.utcnow()
        
        await db.execute(
            Session.__table__.update()
            .where(Session.email_address_id == email_address_id, Session.is_active == True)
            .values(expires_at=email_address.expires_at)
        )
        
        await db.commit()
        await db.refresh(email_address)
        return email_address
    
    async def get_stats(
        self,
        db: AsyncSession,
        email_address_id: str,
    ) -> Dict[str, Any]:
        total = await db.scalar(
            select(func.count(Email.id)).where(Email.email_address_id == email_address_id)
        )
        
        unread = await db.scalar(
            select(func.count(Email.id)).where(
                Email.email_address_id == email_address_id,
                Email.status == "received",
            )
        )
        
        result = await db.execute(
            select(EmailAddress).where(EmailAddress.id == email_address_id)
        )
        email_address = result.scalar_one_or_none()
        
        return {
            "total_emails": total or 0,
            "unread_emails": unread or 0,
            "remaining_slots": (email_address.max_emails - (total or 0)) if email_address else 0,
            "expires_at": email_address.expires_at if email_address else None,
            "is_expired": email_address.expires_at < datetime.utcnow() if email_address else True,
        }
    
    def hash_password(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        import secrets
        return secrets.compare_digest(self.hash_password(plain), hashed)
    
    def generate_token(self, length: int = 32) -> str:
        import secrets
        return secrets.token_urlsafe(length)
    
    async def send_test_email(
        self,
        to_address: str,
        from_address: str = "test@tempmail.pro",
        subject: str = "Test Email",
        body: str = "This is a test email",
    ) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = from_address
            msg["To"] = to_address
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send test email: {e}")
            return False
    
    async def start_smtp_server(self):
        # This would be implemented with aiosmtpd in production
        pass