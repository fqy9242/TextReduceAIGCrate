from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TaskLog


async def add_task_log(
    session: AsyncSession,
    *,
    task_id: str,
    message: str,
    level: str = "info",
    stage: str = "worker",
    detail: dict[str, Any] | None = None,
    commit: bool = False,
) -> None:
    session.add(
        TaskLog(
            task_id=task_id,
            level=level[:16],
            stage=stage[:32],
            message=message[:4000],
            detail=detail or {},
        )
    )
    if commit:
        await session.commit()
