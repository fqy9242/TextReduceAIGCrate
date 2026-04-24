from __future__ import annotations

from pathlib import Path

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


def test_prompt_manager_updates_prompt_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "style_demo.yaml"
    prompt_file.write_text(
        "\n".join(
            [
                "group: style",
                "name: demo",
                "version: \"1.0.0\"",
                "variables:",
                "  - text",
                "instruction: |",
                "  old instruction",
                "",
            ]
        ),
        encoding="utf-8",
    )

    manager = PromptManager(tmp_path)
    manager.update_prompt(
        group="style",
        name="demo",
        version="1.0.1",
        variables=["text", "text", " tone "],
        system="",
        human="",
        instruction="new instruction",
    )

    updated = manager.get_prompt("style", "demo")
    assert updated.version == "1.0.1"
    assert updated.variables == ["text", "tone"]
    assert updated.instruction == "new instruction"
