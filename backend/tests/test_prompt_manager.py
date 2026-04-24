from __future__ import annotations

from app.core.config import get_settings
from app.services.prompt_manager import PromptManager


def test_prompt_manager_loads_and_validates() -> None:
    settings = get_settings()
    manager = PromptManager(settings.prompts_root)
    items = manager.list_metadata()
    assert len(items) >= 3

    rewrite = manager.get_prompt("rewrite", "deai_external")
    assert rewrite.version
    assert "original_text" in rewrite.variables
    assert rewrite.system
    assert rewrite.human
