from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.models import RewriteTask, User
from app.db.session import AsyncSessionFactory
from app.services.task_worker import TaskWorker


class SlowRewriteAgent:
    async def run_task(self, session, task) -> None:  # noqa: ANN001
        await asyncio.sleep(2)


class CrashRewriteAgent:
    async def run_task(self, session, task) -> None:  # noqa: ANN001
        raise RuntimeError("mock agent crash")


@pytest.mark.asyncio
async def test_worker_marks_task_failed_on_timeout() -> None:
    agent = SlowRewriteAgent()
    worker = TaskWorker(
        session_factory=AsyncSessionFactory,
        rewrite_agent=agent,  # type: ignore[arg-type]
        execution_timeout_seconds=1,
    )

    async with AsyncSessionFactory() as session:
        user = User(username=f"user_{uuid.uuid4().hex[:8]}", password_hash=hash_password("password"))
        task = RewriteTask(
            user=user,
            input_text="这是一段用于验证任务执行超时处理逻辑的文本，长度足够。",
            target_score=20,
            max_rounds=3,
            style="deai_external",
            status="queued",
        )
        session.add_all([user, task])
        await session.commit()
        await session.refresh(task)

    await worker._process_task(task.id)

    async with AsyncSessionFactory() as session:
        loaded = await session.scalar(
            select(RewriteTask)
            .options(selectinload(RewriteTask.logs))
            .where(RewriteTask.id == task.id)
        )

    assert loaded is not None
    assert loaded.status == "failed"
    assert loaded.error_message is not None
    assert "timeout" in loaded.error_message.lower()
    assert len(loaded.logs) >= 2


@pytest.mark.asyncio
async def test_worker_marks_task_failed_on_agent_exception() -> None:
    agent = CrashRewriteAgent()
    worker = TaskWorker(
        session_factory=AsyncSessionFactory,
        rewrite_agent=agent,  # type: ignore[arg-type]
        execution_timeout_seconds=5,
    )

    async with AsyncSessionFactory() as session:
        user = User(username=f"user_{uuid.uuid4().hex[:8]}", password_hash=hash_password("password"))
        task = RewriteTask(
            user=user,
            input_text="这是一段用于验证任务执行异常处理逻辑的文本，长度足够。",
            target_score=20,
            max_rounds=3,
            style="deai_external",
            status="queued",
        )
        session.add_all([user, task])
        await session.commit()
        await session.refresh(task)

    await worker._process_task(task.id)

    async with AsyncSessionFactory() as session:
        loaded = await session.scalar(
            select(RewriteTask)
            .options(selectinload(RewriteTask.logs))
            .where(RewriteTask.id == task.id)
        )

    assert loaded is not None
    assert loaded.status == "failed"
    assert loaded.error_message is not None
    assert "mock agent crash" in loaded.error_message
    assert len(loaded.logs) >= 2
