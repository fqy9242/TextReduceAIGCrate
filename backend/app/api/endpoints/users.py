from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db_session, require_permission
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Role, User
from app.schemas.user import CreateUserRequest, UpdateUserRoleRequest, UserOut
from app.services.audit import write_audit_log
from app.services.rbac import PERM_USER_MANAGE


router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
    )


@router.get("", response_model=list[UserOut])
async def list_users(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission(PERM_USER_MANAGE)),
) -> list[UserOut]:
    users = (
        await session.scalars(select(User).options(selectinload(User.roles)).order_by(User.id.asc()))
    ).all()
    return [_to_user_out(user) for user in users]


@router.post("", response_model=UserOut)
async def create_user(
    payload: CreateUserRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_permission(PERM_USER_MANAGE)),
) -> UserOut:
    exists = await session.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    role = await session.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    user.roles.append(role)
    session.add(user)
    await write_audit_log(
        session,
        action="user.create",
        user_id=admin.id,
        detail={"username": payload.username, "role": payload.role},
    )
    await session.commit()
    await session.refresh(user)

    loaded = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    assert loaded is not None
    return _to_user_out(loaded)


@router.patch("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_permission(PERM_USER_MANAGE)),
) -> UserOut:
    user = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.username == settings.admin_bootstrap_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap admin account role is immutable",
        )

    role = await session.scalar(select(Role).where(Role.name == payload.role))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found")

    user.roles.clear()
    user.roles.append(role)
    await write_audit_log(
        session,
        action="user.role_update",
        user_id=admin.id,
        detail={"target_user_id": user_id, "role": payload.role},
    )
    await session.commit()
    await session.refresh(user)
    loaded = await session.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user.id)
    )
    assert loaded is not None
    return _to_user_out(loaded)
