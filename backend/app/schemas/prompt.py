from __future__ import annotations

from pydantic import BaseModel


class PromptMetadata(BaseModel):
    group: str
    name: str
    version: str
    variables: list[str]
    file_path: str


class PromptMetadataResponse(BaseModel):
    items: list[PromptMetadata]

