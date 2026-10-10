from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional
import re

from app.db.database import get_db
from app.api.v1.dependencies import get_current_email_address, get_optional_email_address
from app.core.exceptions import NotFoundError, ConflictError
from app.models.models import Email, EmailAddress, Attachment
from app.schemas.schemas import (
    EmailResponse, EmailList, EmailDetail,
    EmailFilterParams, PaginationParams,
    OTPResponse, VerificationLinkResponse,
)
from app.services.email_parser import EmailParser
from app.services.otp_service import OTPService


router = APIRouter()
otp_extractor = OTPService()
email_parser = EmailParser()


@router.get("", response_model=EmailList)
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    search: Optional[str] = Query(None),
    from_address: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    query = select(Email).where(Email.email_address_id == current_email.id)
    
    if status:
        query = query.where(Email.status == status)
    
    if unread_only:
        query = query.where(Email.status == "received")
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Email.subject.ilike(search_term),
                Email.from_address.ilike(search_term),
                Email.text_body.ilike(search_term),
            )
        )
    
    if from_address:
        query = query.where(Email.from_address.ilike(f"%{from_address}%"))
    
    if date_from:
        query = query.where(Email.received_at >= date_from)
    
    if date_to:
        query = query.where(Email.received_at <= date_to)
    
    query = query.order_by(Email.received_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return EmailList(
        emails=[EmailResponse.model_validate(e) for e in emails],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    count = await db.scalar(
        select(func.count(Email.id)).where(
            Email.email_address_id == current_email.id,
            Email.status == "received",
        )
    )
    return {"unread_count": count or 0}


@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    if email.status == "received":
        email.status = "read"
        email.read_at = datetime.utcnow()
        await db.commit()
    
    otp_codes = otp_extractor.extract_otp_codes(
        email.text_body or "",
        email.html_body or "",
        email.subject or ""
    )
    
    verification_links = otp_extractor.extract_verification_links(
        email.text_body or "",
        email.html_body or "",
    )
    
    return EmailDetail(
        **EmailResponse.model_validate(email).model_dump(),
        otp_codes=otp_codes,
        verification_links=verification_links,
    )


@router.get("/{email_id}/source")
async def get_email_source(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    return {"raw_source": email.raw_source or ""}


@router.get("/{email_id}/otp", response_model=OTPResponse)
async def get_email_otp(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    otp_codes = otp_extractor.extract_otp_codes(
        email.text_body or "",
        email.html_body or "",
        email.subject or ""
    )
    
    primary_otp = otp_codes[0]["code"] if otp_codes else None
    
    return OTPResponse(
        email_id=email_id,
        otp_codes=otp_codes,
        primary_otp=primary_otp,
        count=len(otp_codes),
    )


@router.get("/{email_id}/verification-links", response_model=VerificationLinkResponse)
async def get_verification_links(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    links = otp_extractor.extract_verification_links(
        email.text_body or "",
        email.html_body or "",
    )
    
    return VerificationLinkResponse(
        email_id=email_id,
        links=links,
        count=len(links),
    )


@router.delete("/{email_id}", response_model=dict)
async def delete_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    email.status = "deleted"
    email.deleted_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Email deleted successfully", "id": email_id}


@router.delete("", response_model=dict)
async def delete_all_emails(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    query = delete(Email).where(Email.email_address_id == current_email.id)
    
    if status:
        query = query.where(Email.status == status)
    
    result = await db.execute(query)
    await db.commit()
    
    return {"message": f"Deleted {result.rowcount} emails", "deleted_count": result.rowcount}


@router.post("/{email_id}/read", response_model=dict)
async def mark_as_read(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Email).where(
            Email.id == email_id,
            Email.email_address_id == current_email.id,
        )
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise NotFoundError("Email not found")
    
    if email.status == "received":
        email.status = "read"
        email.read_at = datetime.utcnow()
        await db.commit()
    
    return {"message": "Email marked as read", "id": email_id}


@router.get("/{email_id}/attachments")
async def get_attachments(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Attachment).where(
            Attachment.email_id == email_id,
        )
    )
    attachments = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "filename": a.filename,
            "content_type": a.content_type,
            "size": a.size,
            "content_id": a.content_id,
            "is_inline": a.is_inline,
        }
        for a in attachments
    ]


@router.get("/{email_id}/inbox", response_model=EmailList)
async def get_inbox(
    email_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    query = select(Email).where(Email.email_address_id == current_email.id, Email.status != "deleted")

    if status:
        query = query.where(Email.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Email.subject.ilike(search_term),
                Email.from_address.ilike(search_term),
                Email.text_body.ilike(search_term),
            )
        )

    query = query.order_by(Email.received_at.desc())
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    emails = result.scalars().all()

    return EmailList(
        emails=[EmailResponse.model_validate(e) for e in emails],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.delete("/{email_id}/emails/{message_id}", response_model=dict)
async def delete_email_by_address(
    email_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    result = await db.execute(
        select(Email).where(Email.id == message_id, Email.email_address_id == current_email.id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    email.status = "deleted"
    email.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Email deleted successfully", "id": message_id}


@router.delete("/{email_id}/emails", response_model=dict)
async def delete_all_emails_by_address(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    query = delete(Email).where(Email.email_address_id == current_email.id)
    result = await db.execute(query)
    await db.commit()
    return {"message": f"Deleted {result.rowcount} emails", "deleted_count": result.rowcount}


@router.get("/{email_id}/emails/{message_id}", response_model=EmailDetail)
async def get_email_by_address(
    email_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    result = await db.execute(
        select(Email).where(Email.id == message_id, Email.email_address_id == current_email.id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    if email.status == "received":
        email.status = "read"
        email.read_at = datetime.utcnow()
        await db.commit()

    otp_codes = otp_extractor.extract_otp_codes(
        email.text_body or "", email.html_body or "", email.subject or ""
    )
    verification_links = otp_extractor.extract_verification_links(
        email.text_body or "", email.html_body or ""
    )

    return EmailDetail(
        **EmailResponse.model_validate(email).model_dump(),
        otp_codes=otp_codes,
        verification_links=verification_links,
    )


@router.post("/{email_id}/emails/{message_id}/read", response_model=dict)
async def mark_as_read_by_address(
    email_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    result = await db.execute(
        select(Email).where(Email.id == message_id, Email.email_address_id == current_email.id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    if email.status == "received":
        email.status = "read"
        email.read_at = datetime.utcnow()
        await db.commit()

    return {"message": "Email marked as read", "id": message_id}


@router.get("/{email_id}/emails/{message_id}/otp", response_model=OTPResponse)
async def get_email_otp_by_address(
    email_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    result = await db.execute(
        select(Email).where(Email.id == message_id, Email.email_address_id == current_email.id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise NotFoundError("Email not found")

    otp_codes = otp_extractor.extract_otp_codes(
        email.text_body or "", email.html_body or "", email.subject or ""
    )
    primary_otp = otp_codes[0]["code"] if otp_codes else None

    return OTPResponse(
        email_id=message_id,
        otp_codes=otp_codes,
        primary_otp=primary_otp,
        count=len(otp_codes),
    )


@router.get("/{email_id}/timer")
async def get_timer(
    email_id: str,
    current_email: EmailAddress = Depends(get_current_email_address),
):
    if str(current_email.id) != email_id:
        raise NotFoundError("Email address not found")

    now = datetime.utcnow()
    expires_at = current_email.expires_at
    expired = expires_at <= now
    seconds_remaining = max(0, int((expires_at - now).total_seconds())) if not expired else 0
    hours = seconds_remaining // 3600
    minutes = (seconds_remaining % 3600) // 60
    seconds = seconds_remaining % 60

    return {
        "expired": expired,
        "expires_at": expires_at.isoformat(),
        "seconds_remaining": seconds_remaining,
        "formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
    }
