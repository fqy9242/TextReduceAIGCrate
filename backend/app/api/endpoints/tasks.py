from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, get_user_role_names, require_permission
from app.db.models import RewriteTask, TaskIteration, User
from app.schemas.task import (
    TaskCreateRequest,
    TaskIterationOut,
    TaskListItemOut,
    TaskListResponse,
    TaskResultOut,
)
from app.services.audit import write_audit_log
from app.services.rbac import (
    PERM_TASK_CREATE,
    PERM_TASK_EXPORT_ALL,
    PERM_TASK_EXPORT_OWN,
    PERM_TASK_READ_ALL,
    PERM_TASK_READ_OWN,
    has_permission,
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


def _iteration_to_schema(item: TaskIteration) -> TaskIterationOut:
    llm_mode = None
    if isinstance(item.detector_raw, dict):
        llm_mode = item.detector_raw.get("llm_mode")
    return TaskIterationOut(
        round=item.round_index,
        prompt_version=item.prompt_version,
        rewritten_text=item.rewritten_text,
        detector_score=item.detector_score,
        detector_label=item.detector_label,
        llm_mode=llm_mode,
        latency_ms=item.latency_ms,
        created_at=item.created_at,
    )


def _task_to_result_schema(task: RewriteTask) -> TaskResultOut:
    iterations = [_iteration_to_schema(item) for item in task.iterations]
    return TaskResultOut(
        id=task.id,
        status=task.status,
        input_text=task.input_text,
        best_text=task.best_text,
        best_score=task.best_score,
        met_target=task.met_target,
        target_score=task.target_score,
        max_rounds=task.max_rounds,
        rounds_used=task.rounds_used,
        style=task.style,
        created_at=task.created_at,
        completed_at=task.completed_at,
        iterations=iterations,
    )


def _can_read_all(user: User) -> bool:
    return has_permission(get_user_role_names(user), PERM_TASK_READ_ALL)


def _can_read_own(user: User) -> bool:
    return has_permission(get_user_role_names(user), PERM_TASK_READ_OWN)


def _can_export_all(user: User) -> bool:
    return has_permission(get_user_role_names(user), PERM_TASK_EXPORT_ALL)


def _can_export_own(user: User) -> bool:
    return has_permission(get_user_role_names(user), PERM_TASK_EXPORT_OWN)


def _check_task_read_access(task: RewriteTask, user: User) -> None:
    if _can_read_all(user):
        return
    if _can_read_own(user) and task.user_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission for this task")


def _check_task_export_access(task: RewriteTask, user: User) -> None:
    if _can_export_all(user):
        return
    if _can_export_own(user) and task.user_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to export this task")


@router.post("", response_model=TaskResultOut)
async def create_task(
    payload: TaskCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(require_permission(PERM_TASK_CREATE)),
) -> TaskResultOut:
    task = RewriteTask(
        user_id=user.id,
        input_text=payload.input_text,
        target_score=payload.target_score,
        max_rounds=payload.max_rounds,
        style=payload.style,
        status="queued",
        created_at=datetime.now(timezone.utc),
    )
    session.add(task)
    await write_audit_log(
        session,
        action="task.create",
        user_id=user.id,
        detail={"target_score": payload.target_score, "max_rounds": payload.max_rounds, "style": payload.style},
    )
    await session.commit()
    await session.refresh(task)

    await request.app.state.task_worker.enqueue(task.id)
    return TaskResultOut(
        id=task.id,
        status=task.status,
        input_text=task.input_text,
        best_text=task.best_text,
        best_score=task.best_score,
        met_target=task.met_target,
        target_score=task.target_score,
        max_rounds=task.max_rounds,
        rounds_used=task.rounds_used,
        style=task.style,
        created_at=task.created_at,
        completed_at=task.completed_at,
        iterations=[],
    )


@router.get("/{task_id}", response_model=TaskResultOut)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> TaskResultOut:
    task = await session.scalar(
        select(RewriteTask)
        .options(selectinload(RewriteTask.iterations))
        .where(RewriteTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _check_task_read_access(task, user)
    return _task_to_result_schema(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> TaskListResponse:
    offset = (page - 1) * page_size
    base_query = select(RewriteTask)
    count_query = select(func.count(RewriteTask.id))

    if not _can_read_all(user):
        if not _can_read_own(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to read tasks")
        base_query = base_query.where(RewriteTask.user_id == user.id)
        count_query = count_query.where(RewriteTask.user_id == user.id)

    tasks = (
        await session.scalars(
            base_query.order_by(RewriteTask.created_at.desc()).offset(offset).limit(page_size)
        )
    ).all()
    total = await session.scalar(count_query)

    items = [
        TaskListItemOut(
            id=item.id,
            status=item.status,
            target_score=item.target_score,
            best_score=item.best_score,
            met_target=item.met_target,
            rounds_used=item.rounds_used,
            style=item.style,
            created_at=item.created_at,
            completed_at=item.completed_at,
        )
        for item in tasks
    ]
    return TaskListResponse(items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/{task_id}/export")
async def export_task_result(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> PlainTextResponse:
    task = await session.scalar(
        select(RewriteTask)
        .options(selectinload(RewriteTask.iterations))
        .where(RewriteTask.id == task_id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    _check_task_export_access(task, user)

    lines = [
        f"Task ID: {task.id}",
        f"Status: {task.status}",
        f"Target Score: {task.target_score}",
        f"Best Score: {task.best_score}",
        f"Met Target: {task.met_target}",
        f"Rounds Used: {task.rounds_used}",
        "",
        "Original Text:",
        task.input_text,
        "",
        "Best Rewritten Text:",
        task.best_text or "",
        "",
        "Iterations:",
    ]
    for item in task.iterations:
        lines.extend(
            [
                f"- Round {item.round_index} | score={item.detector_score} | label={item.detector_label}",
                item.rewritten_text,
                "",
            ]
        )
    content = "\n".join(lines)
    return PlainTextResponse(content=content, media_type="text/plain; charset=utf-8")
