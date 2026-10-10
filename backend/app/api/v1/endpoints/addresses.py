from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from uuid import uuid4
import secrets
import string

from app.db.database import get_db
from app.api.v1.dependencies import get_current_session, get_current_email_address
from app.core.exceptions import (
    NotFoundError, ValidationError, ConflictError,
    DomainNotAllowedError, MaxEmailsReachedError
)
from app.models.models import EmailAddress, Domain, Session
from app.schemas.schemas import (
    EmailAddressCreate, EmailAddressResponse, EmailAddressUpdate,
    GenerateEmailRequest, GenerateEmailResponse,
    SessionResponse, StatsResponse,
)
from app.services.email_service import EmailService
from app.core.config import settings

router = APIRouter()
email_service = EmailService()


def generate_random_local_part(length: int = 10) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("/generate", response_model=GenerateEmailResponse)
async def generate_email(
    request: GenerateEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    addresses = []
    tokens = []
    
    for _ in range(request.count):
        domain = request.domain or settings.DEFAULT_DOMAINS[0]
        
        result = await db.execute(select(Domain).where(Domain.domain == domain))
        domain_obj = result.scalar_one_or_none()
        
        if not domain_obj or not domain_obj.is_active:
            raise DomainNotAllowedError(domain, settings.DEFAULT_DOMAINS)
        
        prefix = request.prefix or generate_random_local_part(8)
        
        existing = await db.execute(
            select(EmailAddress).where(
                EmailAddress.local_part == prefix,
                EmailAddress.domain == domain,
            )
        )
        if existing.scalar_one_or_none():
            prefix = f"{prefix}{secrets.randbelow(1000):03d}"
        
        ttl_hours = request.ttl_hours or settings.DEFAULT_TTL_HOURS
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        email_address = EmailAddress(
            email=f"{prefix}@{domain}",
            local_part=prefix,
            domain=domain,
            status="active",
            expires_at=expires_at,
            max_emails=settings.DEFAULT_MAX_EMAILS,
            is_custom=bool(request.prefix),
            token=generate_token(),
        )
        
        db.add(email_address)
        await db.flush()
        
        session_token = generate_token()
        session = Session(
            email_address_id=email_address.id,
            token=session_token,
            expires_at=expires_at,
            is_active=True,
        )
        db.add(session)
        
        await db.commit()
        await db.refresh(email_address)
        
        addresses.append(EmailAddressResponse.model_validate(email_address))
        tokens.append(session_token)
    
    primary = addresses[0] if addresses else None
    return GenerateEmailResponse(
        email=primary,
        token=tokens[0] if tokens else None,
        expires_at=expires_at,
        addresses=addresses,
    )


@router.post("", response_model=EmailAddressResponse)
async def create_email_address(
    data: EmailAddressCreate,
    db: AsyncSession = Depends(get_db),
):
    if data.domain:
        result = await db.execute(select(Domain).where(Domain.domain == data.domain))
        domain_obj = result.scalar_one_or_none()
        if not domain_obj or not domain_obj.is_active:
            raise DomainNotAllowedError(data.domain, settings.DEFAULT_DOMAINS)
        domain = data.domain
    else:
        domain = settings.DEFAULT_DOMAINS[0]
    
    if data.local_part:
        existing = await db.execute(
            select(EmailAddress).where(
                EmailAddress.local_part == data.local_part,
                EmailAddress.domain == domain,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email address {data.local_part}@{domain} already exists")
        local_part = data.local_part
    else:
        local_part = generate_random_local_part(10)
        while True:
            existing = await db.execute(
                select(EmailAddress).where(
                    EmailAddress.local_part == local_part,
                    EmailAddress.domain == domain,
                )
            )
            if not existing.scalar_one_or_none():
                break
            local_part = generate_random_local_part(10)
    
    ttl_hours = data.ttl_hours or settings.DEFAULT_TTL_HOURS
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    email_address = EmailAddress(
        email=f"{local_part}@{domain}",
        local_part=local_part,
        domain=domain,
        status="active",
        expires_at=expires_at,
        max_emails=data.max_emails or settings.DEFAULT_MAX_EMAILS,
        is_custom=bool(data.local_part or data.domain),
        token=generate_token(),
    )
    
    db.add(email_address)
    await db.flush()
    
    session = Session(
        email_address_id=email_address.id,
        token=generate_token(),
        expires_at=expires_at,
        is_active=True,
    )
    db.add(session)
    
    await db.commit()
    await db.refresh(email_address)
    
    return EmailAddressResponse.model_validate(email_address)


@router.get("", response_model=list[EmailAddressResponse])
async def list_email_addresses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_session: Session = Depends(get_current_session),
):
    query = select(EmailAddress).where(EmailAddress.id == current_session.email_address_id)
    
    if status:
        query = query.where(EmailAddress.status == status)
    
    query = query.order_by(EmailAddress.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    addresses = result.scalars().all()
    
    return [EmailAddressResponse.model_validate(a) for a in addresses]


@router.get("/domains", response_model=list[dict])
async def list_domains(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Domain).where(Domain.is_active == True).order_by(Domain.domain)
    )
    domains = result.scalars().all()
    
    return [
        {
            "domain": d.domain,
            "is_default": d.is_default,
            "emails_received": d.emails_received,
        }
        for d in domains
    ]


@router.get("/{email_id}", response_model=EmailAddressResponse)
async def get_email_address(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")
    
    return EmailAddressResponse.model_validate(current_email)


@router.patch("/{email_id}", response_model=EmailAddressResponse)
async def update_email_address(
    email_id: str,
    data: EmailAddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")
    
    if current_email.status != "active":
        raise EmailAddressExpiredError(current_email.email)
    
    if data.password is not None:
        current_email.password_hash = email_service.hash_password(data.password)
    
    if data.max_emails is not None:
        current_email.max_emails = min(data.max_emails, settings.MAX_EMAILS_PER_ADDRESS)
    
    if data.ttl_hours is not None:
        if current_email.expires_at > datetime.utcnow():
            current_email.expires_at = datetime.utcnow() + timedelta(hours=data.ttl_hours)
    
    current_email.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_email)
    
    return EmailAddressResponse.model_validate(current_email)


@router.delete("/{email_id}", response_model=dict)
async def delete_email_address(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")
    
    current_email.status = "deleted"
    current_email.deleted_at = datetime.utcnow()
    
    await db.execute(
        Session.__table__.update()
        .where(Session.email_address_id == current_email.id)
        .values(is_active=False)
    )
    
    await db.commit()
    
    return {"message": f"Email address {current_email.email} deleted"}


@router.post("/{email_id}/renew", response_model=EmailAddressResponse)
async def renew_email_address(
    email_id: str,
    ttl_hours: int = Query(settings.DEFAULT_TTL_HOURS, ge=1, le=settings.MAX_TTL_HOURS),
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")
    
    if current_email.status != "active":
        raise EmailAddressExpiredError(current_email.email)
    
    current_email.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    current_email.updated_at = datetime.utcnow()
    
    await db.execute(
        Session.__table__.update()
        .where(Session.email_address_id == current_email.id, Session.is_active == True)
        .values(expires_at=current_email.expires_at)
    )
    
    await db.commit()
    await db.refresh(current_email)
    
    return EmailAddressResponse.model_validate(current_email)


@router.get("/{email_id}/stats", response_model=StatsResponse)
async def get_email_stats(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")
    
    total_emails = await db.scalar(
        select(func.count(Email.id)).where(Email.email_address_id == current_email.id)
    )
    
    today_emails = await db.scalar(
        select(func.count(Email.id)).where(
            Email.email_address_id == current_email.id,
            Email.received_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        )
    )
    
    return StatsResponse(
        total_emails=total_emails,
        emails_today=today_emails,
        emails_this_week=0,
        emails_this_month=0,
        max_emails=current_email.max_emails,
        remaining_emails=max(0, current_email.max_emails - total_emails),
        expires_at=current_email.expires_at,
        is_expired=current_email.expires_at <= datetime.utcnow(),
    )