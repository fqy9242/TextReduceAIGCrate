from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_async_session
from app.services.rbac import has_permission


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db_session(session: AsyncSession = Depends(get_async_session)) -> AsyncSession:
    return session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub", 0))
        token_version = int(payload.get("token_version", -1))
    except (ValueError, JWTError):
        raise credentials_error

    user = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if user is None or not user.is_active:
        raise credentials_error
    if user.token_version != token_version:
        raise credentials_error
    return user


def get_user_role_names(user: User) -> list[str]:
    return [role.name for role in user.roles]


def require_permission(permission: str) -> Callable:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not has_permission(get_user_role_names(user), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return dependency

