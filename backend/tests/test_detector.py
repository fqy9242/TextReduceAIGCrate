from __future__ import annotations

import pytest

from app.services.detectors import normalize_label


def test_normalize_label_standardization() -> None:
    assert normalize_label("AI") == "ai_like"
    assert normalize_label("human") == "human_like"
    assert normalize_label("unknown") == "uncertain"
