from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock

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
            if group == "rewrite" and (not system or not human):
                raise ValueError(f"Rewrite prompt must contain system + human in {file_path}")

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

