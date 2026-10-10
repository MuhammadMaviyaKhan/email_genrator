from fastapi import APIRouter, Depends, Query, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import hashlib
import secrets

from app.db.database import get_db
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, NotFoundError
from app.models.models import (
    EmailAddress, Email, Domain, AuditLog, Session
)
from app.schemas.schemas import (
    EmailAddressResponse, EmailList, StatsResponse,
    HealthResponse,
)
from app.core.security.security import verify_token, generate_secure_token


router = APIRouter()


async def verify_admin_token(
    x_admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> dict:
    token = x_admin_token

    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")

    if not token:
        raise UnauthorizedError("Admin token required")

    expected = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    if not secrets.compare_digest(token, expected):
        payload = verify_token(token)
        if not payload or payload.get("role") != "admin":
            raise UnauthorizedError("Invalid admin token")

    return {"role": "admin", "authenticated": True}


@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    total_addresses = await db.scalar(select(func.count(EmailAddress.id)))
    active_addresses = await db.scalar(
        select(func.count(EmailAddress.id)).where(
            EmailAddress.status == "active",
            EmailAddress.expires_at > datetime.utcnow(),
        )
    )
    expired_addresses = await db.scalar(
        select(func.count(EmailAddress.id)).where(EmailAddress.status == "expired")
    )
    total_emails = await db.scalar(select(func.count(Email.id)))
    emails_today = await db.scalar(
        select(func.count(Email.id)).where(
            Email.received_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        )
    )
    emails_this_week = await db.scalar(
        select(func.count(Email.id)).where(
            Email.received_at >= datetime.utcnow() - timedelta(days=7)
        )
    )
    emails_this_month = await db.scalar(
        select(func.count(Email.id)).where(
            Email.received_at >= datetime.utcnow() - timedelta(days=30)
        )
    )
    active_domains = await db.scalar(
        select(func.count(Domain.id)).where(Domain.is_active == True)
    )
    total_domains = await db.scalar(select(func.count(Domain.id)))

    return StatsResponse(
        total_addresses=total_addresses or 0,
        active_addresses=active_addresses or 0,
        expired_addresses=expired_addresses or 0,
        total_emails=total_emails or 0,
        emails_today=emails_today or 0,
        emails_this_week=emails_this_week or 0,
        emails_this_month=emails_this_month or 0,
        active_domains=active_domains or 0,
        total_domains=total_domains or 0,
    )


@router.get("/emails", response_model=EmailList)
async def list_all_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    query = select(EmailAddress)

    if search:
        search_term = f"%{search}%"
        query = query.where(EmailAddress.email.ilike(search_term))

    if status:
        query = query.where(EmailAddress.status == status)

    query = query.order_by(desc(EmailAddress.created_at))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    addresses = result.scalars().all()

    return EmailList(
        emails=[EmailAddressResponse.model_validate(a) for a in addresses],
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.delete("/emails/{email_id}")
async def delete_email_address_admin(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.id == email_id)
    )
    email_address = result.scalar_one_or_none()

    if not email_address:
        raise NotFoundError("Email address not found")

    await db.delete(email_address)
    await db.commit()

    return {"message": f"Email address {email_address.email} deleted", "id": email_id}


@router.get("/emails/{email_id}/messages", response_model=EmailList)
async def list_email_messages_admin(
    email_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.id == email_id)
    )
    email_address = result.scalar_one_or_none()

    if not email_address:
        raise NotFoundError("Email address not found")

    query = select(Email).where(Email.email_address_id == email_id)
    query = query.order_by(desc(Email.received_at))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    emails = result.scalars().all()

    return EmailList(
        emails=emails,
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.get("/logs", response_model=dict)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    query = select(AuditLog)

    if level:
        query = query.where(AuditLog.level == level)
    if event_type:
        query = query.where(AuditLog.event_type.ilike(f"%{event_type}%"))
    if search:
        query = query.where(AuditLog.message.ilike(f"%{search}%"))

    query = query.order_by(desc(AuditLog.created_at))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": str(log.id),
                "level": log.level,
                "event_type": log.event_type,
                "message": log.message,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_id": str(log.user_id) if log.user_id else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/logs/export")
async def export_logs(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    result = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)))
    logs = result.scalars().all()

    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "total_logs": len(logs),
        "logs": [
            {
                "id": str(log.id),
                "level": log.level,
                "event_type": log.event_type,
                "message": log.message,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }

    return export_data


@router.get("/domains", response_model=list)
async def list_domains_admin(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    result = await db.execute(select(Domain).order_by(Domain.domain))
    domains = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "domain": d.domain,
            "is_active": d.is_active,
            "is_default": d.is_default,
            "emails_received": d.emails_received,
            "created_at": d.created_at.isoformat(),
        }
        for d in domains
    ]


@router.post("/domains")
async def add_domain(
    domain: str,
    is_default: bool = False,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    import re

    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$', domain):
        raise ValueError("Invalid domain format")

    existing = await db.execute(select(Domain).where(Domain.domain == domain))
    if existing.scalar_one_or_none():
        raise ValueError("Domain already exists")

    new_domain = Domain(
        domain=domain,
        is_active=True,
        is_default=is_default,
    )
    db.add(new_domain)
    await db.commit()

    return {"message": f"Domain {domain} added", "domain": domain}


@router.get("/health", response_model=HealthResponse)
async def admin_health(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database="connected",
        redis="not_configured",
        smtp="unknown",
        uptime_seconds=0.0,
        websocket_connections=0,
        active_addresses=0,
    )


@router.get("/system/info")
async def system_info(
    _: dict = Depends(verify_admin_token),
):
    import psutil
    import platform

    return {
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_total": psutil.disk_usage('/').total,
            "disk_free": psutil.disk_usage('/').free,
            "disk_percent": psutil.disk_usage('/').percent,
        },
        "app": {
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
    }
