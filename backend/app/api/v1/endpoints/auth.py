from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

from app.db.database import get_db
from app.api.v1.dependencies import (
    get_current_session, get_current_email_address,
    create_access_token, verify_password, hash_password,
    generate_token, verify_admin_token
)
from app.core.exceptions import UnauthorizedError, NotFoundError, ValidationError
from app.core.config import settings
from app.models.models import EmailAddress, Session
from app.schemas.schemas import (
    LoginRequest, LoginResponse, TokenResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    SessionResponse, SessionList,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.email == request.email)
    )
    email_address = result.scalar_one_or_none()
    
    if not email_address:
        raise NotFoundError("Email address not found")
    
    if email_address.status != "active":
        raise ValidationError(f"Email address is {email_address.status}")
    
    if email_address.expires_at < datetime.utcnow():
        email_address.status = "expired"
        await db.commit()
        raise ValidationError("Email address has expired")
    
    if email_address.password_hash:
        if not request.password:
            raise ValidationError("Password required")
        if not verify_password(request.password, email_address.password_hash):
            raise ValidationError("Invalid password")
    
    access_token = create_access_token(
        data={"sub": str(email_address.id), "email": email_address.email}
    )
    
    session_token = generate_token()
    session = Session(
        email_address_id=email_address.id,
        token=session_token,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        is_active=True,
    )
    db.add(session)
    
    email_address.last_accessed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(email_address)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        email=email_address,
        session_token=session_token,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(
            Session.token == request.refresh_token,
            Session.is_active == True,
        )
    )
    session = result.scalar_one_or_none()
    
    if not session or session.expires_at < datetime.utcnow():
        raise UnauthorizedError("Invalid or expired refresh token")
    
    result = await db.execute(
        select(EmailAddress).where(EmailAddress.id == session.email_address_id)
    )
    email_address = result.scalar_one_or_none()
    
    if not email_address or email_address.status != "active":
        raise UnauthorizedError("Email address not active")
    
    new_access_token = create_access_token(
        data={"sub": str(email_address.id), "email": email_address.email}
    )
    
    session.token = generate_token()
    session.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    await db.commit()
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=dict)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        return {"message": "Logged out"}
    
    result = await db.execute(
        select(Session).where(Session.token == credentials.credentials)
    )
    session = result.scalar_one_or_none()
    
    if session:
        session.is_active = False
        await db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/sessions", response_model=SessionList)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Session).where(
            Session.email_address_id == current_email.id,
            Session.is_active == True,
        ).order_by(Session.created_at.desc())
    )
    sessions = result.scalars().all()
    
    return SessionList(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
    )


@router.delete("/sessions/{session_id}", response_model=dict)
async def revoke_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_email: EmailAddress = Depends(get_current_email_address),
):
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.email_address_id == current_email.id,
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundError("Session not found")
    
    session.is_active = False
    await db.commit()
    
    return {"message": "Session revoked"}


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        password = body.get("password", "") if isinstance(body, dict) else ""
    except Exception:
        password = ""

    if password != settings.ADMIN_PASSWORD:
        raise UnauthorizedError("Invalid admin password")
    
    access_token = create_access_token(
        data={"sub": "admin", "role": "admin"},
        expires_delta=timedelta(minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/admin/verify", response_model=dict)
async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise UnauthorizedError("Token required")
    
    expected = hashlib.sha256(settings.ADMIN_PASSWORD.encode()).hexdigest()
    if not secrets.compare_digest(credentials.credentials, expected):
        raise UnauthorizedError("Invalid admin token")
    
    return {"valid": True, "role": "admin"}