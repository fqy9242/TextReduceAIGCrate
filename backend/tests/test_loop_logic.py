from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import RewriteTask, TaskIteration, User
from app.db.session import AsyncSessionFactory
from app.services.detectors import BaseDetector, DetectorResult
from app.services.llm_rewriter import LLMRewriter
from app.services.prompt_manager import PromptManager
from app.services.rewrite_agent import RewriteAgent


class SequenceDetector(BaseDetector):
    def __init__(self, scores: list[float]):
        self.scores = scores
        self.index = 0

    async def detect(self, text: str) -> DetectorResult:
        score = self.scores[min(self.index, len(self.scores) - 1)]
        self.index += 1
        label = "human_like" if score <= 20 else "ai_like"
        return DetectorResult(score=score, label=label, raw={"score": score})


@pytest.mark.asyncio
async def test_loop_stops_when_target_met() -> None:
    settings = get_settings()
    manager = PromptManager(settings.prompts_root)
    llm = LLMRewriter(settings=settings)
    detector = SequenceDetector([48.0, 18.0, 10.0])
    agent = RewriteAgent(prompt_manager=manager, llm_rewriter=llm, detector=detector)

    async with AsyncSessionFactory() as session:
        user = User(username=f"user_{uuid.uuid4().hex[:8]}", password_hash=hash_password("password1"))
        task = RewriteTask(
            user=user,
            input_text="这是一段测试文本，用于验证任务在达到目标分数后会提前停止，不继续执行后续轮次。",
            target_score=20,
            max_rounds=3,
            style="deai_external",
            status="running",
        )
        session.add_all([user, task])
        await session.commit()
        await session.refresh(task)

        await agent.run_task(session, task)

        loaded_task = await session.scalar(select(RewriteTask).where(RewriteTask.id == task.id))
        rounds = (
            await session.scalars(select(TaskIteration).where(TaskIteration.task_id == task.id))
        ).all()

    assert loaded_task is not None
    assert loaded_task.status == "success"
    assert loaded_task.met_target is True
    assert loaded_task.rounds_used == 2
    assert len(rounds) == 2


@pytest.mark.asyncio
async def test_loop_returns_best_when_not_met() -> None:
    settings = get_settings()
    manager = PromptManager(settings.prompts_root)
    llm = LLMRewriter(settings=settings)
    detector = SequenceDetector([58.0, 44.0, 36.0])
    agent = RewriteAgent(prompt_manager=manager, llm_rewriter=llm, detector=detector)

    async with AsyncSessionFactory() as session:
        user = User(username=f"user_{uuid.uuid4().hex[:8]}", password_hash=hash_password("password2"))
        task = RewriteTask(
            user=user,
            input_text="这里是一段用于验证未达标分支的文本，期望在达到最大轮数后返回最低分版本并标记 not_met。",
            target_score=20,
            max_rounds=3,
            style="deai_external",
            status="running",
        )
        session.add_all([user, task])
        await session.commit()
        await session.refresh(task)

        await agent.run_task(session, task)
        loaded_task = await session.scalar(select(RewriteTask).where(RewriteTask.id == task.id))

    assert loaded_task is not None
    assert loaded_task.status == "not_met"
    assert loaded_task.met_target is False
    assert loaded_task.rounds_used == 3
    assert loaded_task.best_score == 36.0
