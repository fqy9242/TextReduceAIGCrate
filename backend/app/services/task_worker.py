from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import RewriteTask
from app.services.rewrite_agent import RewriteAgent


logger = logging.getLogger(__name__)


class TaskWorker:
    def __init__(self, session_factory: async_sessionmaker, rewrite_agent: RewriteAgent):
        self.session_factory = session_factory
        self.rewrite_agent = rewrite_agent
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await self.recover_pending_tasks()
        self._worker_task = asyncio.create_task(self._worker_loop(), name="rewrite-task-worker")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    async def enqueue(self, task_id: str) -> None:
        await self.queue.put(task_id)

    async def recover_pending_tasks(self) -> None:
        async with self.session_factory() as session:
            result = await session.scalars(
                select(RewriteTask.id).where(RewriteTask.status.in_(["queued", "running"]))
            )
            for task_id in result.all():
                await self.queue.put(task_id)

    async def _worker_loop(self) -> None:
        while self._running:
            task_id = await self.queue.get()
            try:
                await self._process_task(task_id)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.exception("Task worker loop failed for task_id=%s: %s", task_id, exc)
                await self._mark_task_failed(task_id, str(exc))
            finally:
                self.queue.task_done()

    async def _process_task(self, task_id: str) -> None:
        async with self.session_factory() as session:
            task = await session.scalar(select(RewriteTask).where(RewriteTask.id == task_id))
            if task is None:
                return
            if task.status not in {"queued", "running"}:
                return

            task.status = "running"
            if task.started_at is None:
                task.started_at = datetime.now(timezone.utc)
            await session.commit()

            try:
                await self.rewrite_agent.run_task(session, task)
            except Exception as exc:
                task.status = "failed"
                task.error_message = str(exc)
                task.completed_at = datetime.now(timezone.utc)
                await session.commit()

    async def _mark_task_failed(self, task_id: str, message: str) -> None:
        async with self.session_factory() as session:
            task = await session.scalar(select(RewriteTask).where(RewriteTask.id == task_id))
            if task is None:
                return
            task.status = "failed"
            task.error_message = message[:2000]
            task.completed_at = datetime.now(timezone.utc)
            await session.commit()
