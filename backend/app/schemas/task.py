from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import get_settings


settings = get_settings()


class TaskCreateRequest(BaseModel):
    input_text: str = Field(min_length=20, max_length=20000)
    target_score: float = Field(default=settings.default_target_score, ge=1, le=100)
    max_rounds: int = Field(default=settings.default_max_rounds, ge=1, le=10)
    style: Literal["deai_external"] = Field(default="deai_external")


class TaskIterationOut(BaseModel):
    round: int
    prompt_version: str
    rewritten_text: str
    detector_score: float
    detector_label: str
    llm_mode: str | None = None
    latency_ms: int
    created_at: datetime


class TaskResultOut(BaseModel):
    id: str
    status: str
    input_text: str
    best_text: str | None
    best_score: float | None
    met_target: bool
    target_score: float
    max_rounds: int
    rounds_used: int
    style: str
    created_at: datetime
    completed_at: datetime | None
    iterations: list[TaskIterationOut] = Field(default_factory=list)


class TaskListItemOut(BaseModel):
    id: str
    status: str
    target_score: float
    best_score: float | None
    met_target: bool
    rounds_used: int
    style: str
    created_at: datetime
    completed_at: datetime | None


class TaskListResponse(BaseModel):
    items: list[TaskListItemOut]
    total: int
    page: int
    page_size: int
