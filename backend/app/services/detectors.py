from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass
class DetectorResult:
    score: float
    label: str
    raw: dict


def normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    if normalized in {"ai_like", "ai", "machine", "high_ai"}:
        return "ai_like"
    if normalized in {"human_like", "human", "low_ai"}:
        return "human_like"
    return "uncertain"


class BaseDetector:
    async def detect(self, text: str) -> DetectorResult:
        raise NotImplementedError


class MockDetector(BaseDetector):
    async def detect(self, text: str) -> DetectorResult:
        # Heuristic scoring to simulate a detector for local development.
        length_factor = max(0.0, 35.0 - min(len(text) / 120.0, 35.0))
        punctuation = sum(text.count(p) for p in "，。！？,.!?")
        punctuation_factor = min(20.0, punctuation * 0.35)
        repetition = self._repetition_penalty(text)
        score = max(3.0, min(95.0, 50.0 - length_factor + punctuation_factor + repetition))
        label = "ai_like" if score > 45 else "human_like" if score < 25 else "uncertain"
        return DetectorResult(
            score=round(score, 2),
            label=label,
            raw={"provider": "mock", "length_factor": length_factor, "repetition": repetition},
        )

    def _repetition_penalty(self, text: str) -> float:
        words = [item for item in text.split() if item]
        if not words:
            return 0.0
        unique_ratio = len(set(words)) / len(words)
        return max(0.0, (1.0 - unique_ratio) * 25.0)


class HttpDetector(BaseDetector):
    def __init__(self, endpoint: str, timeout_seconds: int):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    async def detect(self, text: str) -> DetectorResult:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.endpoint, json={"text": text})
            response.raise_for_status()
            payload = response.json()

        score = float(payload.get("score", 100))
        label = normalize_label(str(payload.get("label", "uncertain")))
        return DetectorResult(score=score, label=label, raw=payload)


def build_detector(settings: Settings) -> BaseDetector:
    if settings.detector_provider == "http":
        return HttpDetector(settings.detector_http_url, settings.detector_http_timeout_seconds)
    return MockDetector()

