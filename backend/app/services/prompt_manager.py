from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

import yaml


@dataclass(frozen=True)
class PromptSpec:
    group: str
    name: str
    version: str
    variables: list[str]
    system: str
    human: str
    instruction: str
    file_path: str


class PromptManager:
    def __init__(self, prompts_root: Path):
        self.prompts_root = prompts_root
        self._lock = RLock()
        self._prompts: dict[tuple[str, str], PromptSpec] = {}
        self.reload()

    def reload(self) -> None:
        if not self.prompts_root.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_root}")

        loaded: dict[tuple[str, str], PromptSpec] = {}
        for file_path in sorted(self.prompts_root.glob("*.yaml")):
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            group = str(data.get("group", "")).strip()
            name = str(data.get("name", "")).strip()
            version = str(data.get("version", "")).strip()
            variables = list(data.get("variables", []))
            system = str(data.get("system", "")).strip()
            human = str(data.get("human", "")).strip()
            instruction = str(data.get("instruction", "")).strip()

            if not group or not name or not version:
                raise ValueError(f"Invalid prompt header in {file_path}")
            if group in {"rewrite", "detector"} and (not system or not human):
                raise ValueError(f"{group} prompt must contain system + human in {file_path}")

            spec = PromptSpec(
                group=group,
                name=name,
                version=version,
                variables=variables,
                system=system,
                human=human,
                instruction=instruction,
                file_path=str(file_path),
            )
            loaded[(group, name)] = spec

        with self._lock:
            self._prompts = loaded

    def get_prompt(self, group: str, name: str) -> PromptSpec:
        with self._lock:
            prompt = self._prompts.get((group, name))
        if prompt is None:
            raise KeyError(f"Prompt not found: {group}.{name}")
        return prompt

    def list_metadata(self) -> list[PromptSpec]:
        with self._lock:
            return list(self._prompts.values())

    def update_prompt(
        self,
        *,
        group: str,
        name: str,
        version: str,
        variables: list[str],
        system: str,
        human: str,
        instruction: str,
    ) -> None:
        prompt = self.get_prompt(group, name)
        prompt_path = self._resolve_prompt_path(prompt.file_path)
        backup_content = prompt_path.read_text(encoding="utf-8")

        cleaned_version = version.strip()
        cleaned_variables = self._normalize_variables(variables)
        cleaned_system = system.strip()
        cleaned_human = human.strip()
        cleaned_instruction = instruction.strip()

        if not cleaned_version:
            raise ValueError("Prompt version cannot be empty")

        updated: dict[str, Any] = {
            "group": group,
            "name": name,
            "version": cleaned_version,
            "variables": cleaned_variables,
        }

        if group in {"rewrite", "detector"}:
            if not cleaned_system or not cleaned_human:
                raise ValueError(f"{group} prompt requires non-empty system and human")
            updated["system"] = cleaned_system
            updated["human"] = cleaned_human
            if cleaned_instruction:
                updated["instruction"] = cleaned_instruction
        else:
            if not cleaned_instruction:
                raise ValueError(f"{group} prompt requires non-empty instruction")
            updated["instruction"] = cleaned_instruction

        serialized = yaml.safe_dump(updated, allow_unicode=True, sort_keys=False)
        if not serialized.endswith("\n"):
            serialized += "\n"

        prompt_path.write_text(serialized, encoding="utf-8")
        try:
            self.reload()
        except Exception:
            prompt_path.write_text(backup_content, encoding="utf-8")
            self.reload()
            raise

    @staticmethod
    def _normalize_variables(items: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in items:
            value = str(item).strip()
            if not value or value in seen:
                continue
            normalized.append(value)
            seen.add(value)
        return normalized

    def _resolve_prompt_path(self, file_path: str) -> Path:
        root = self.prompts_root.resolve()
        path = Path(file_path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Prompt file path is outside prompts root") from exc
        return path
