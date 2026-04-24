from __future__ import annotations

from pathlib import Path

from app.services.external_skill_rules import ExternalSkillRulesLoader


def test_external_skill_loader_extracts_numbered_rules(tmp_path: Path) -> None:
    skill_dir = tmp_path / "de-AI-writing"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "\n".join(
            [
                "## 6.5 快速自检清单",
                "1. **而是命中 = 0**",
                "2. **冒号 <= 2**",
                "3. **禁用模板路标**",
                "## 7. 参考文件",
            ]
        ),
        encoding="utf-8",
    )

    loader = ExternalSkillRulesLoader(
        enabled=True,
        repo_root=tmp_path,
        mode="de-AI-writing",
        max_items=2,
    )
    suffix = loader.build_instruction_suffix()

    assert loader.has_rules() is True
    assert "而是命中 = 0" in suffix
    assert "冒号 <= 2" in suffix
    assert "禁用模板路标" not in suffix


def test_external_skill_loader_handles_missing_repo(tmp_path: Path) -> None:
    loader = ExternalSkillRulesLoader(enabled=True, repo_root=tmp_path, mode="missing-mode")
    assert loader.has_rules() is False
    assert loader.build_instruction_suffix() == ""

