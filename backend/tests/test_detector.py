from __future__ import annotations

import pytest

from app.services.detectors import MockDetector, normalize_label


def test_normalize_label_standardization() -> None:
    assert normalize_label("AI") == "ai_like"
    assert normalize_label("human") == "human_like"
    assert normalize_label("unknown") == "uncertain"


@pytest.mark.asyncio
async def test_mock_detector_response_shape() -> None:
    detector = MockDetector()
    result = await detector.detect("这是一段用于检测结构输出的文本，用来验证 score/label/raw 字段存在。")
    assert 0 <= result.score <= 100
    assert result.label in {"ai_like", "human_like", "uncertain"}
    assert isinstance(result.raw, dict)

