from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.models import User
from app.schemas.auth import LoginRequest, MessageResponse, RefreshRequest, TokenResponse
from app.services.audit import write_audit_log


router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_response(user: User) -> TokenResponse:
    settings = get_settings()
    access_token = create_access_token(subject=str(user.id), token_version=user.token_version)
    refresh_token = create_refresh_token(subject=str(user.id), token_version=user.token_version)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    user = await session.scalar(
        select(User)
        .options(selectinload(User.roles))
        .where(User.username == payload.username)
    )
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await write_audit_log(session, action="auth.login", user_id=user.id)
    await session.commit()
    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(decoded.get("sub", 0))
        token_version = int(decoded.get("token_version", -1))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await session.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    await write_audit_log(session, action="auth.refresh", user_id=user.id)
    await session.commit()
    return _build_token_response(user)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    user.token_version += 1
    await write_audit_log(session, action="auth.logout", user_id=user.id)
    await session.commit()
    return MessageResponse(message="Logged out")

