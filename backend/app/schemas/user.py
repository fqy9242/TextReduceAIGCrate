from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool
    roles: list[str]
    created_at: datetime


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(pattern="^(admin|operator|viewer)$")

