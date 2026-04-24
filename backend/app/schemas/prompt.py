from __future__ import annotations

from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    group: str
    name: str
    version: str
    variables: list[str]
    file_path: str


class PromptMetadataResponse(BaseModel):
    items: list[PromptMetadata]


class PromptDetail(BaseModel):
    group: str
    name: str
    version: str
    variables: list[str]
    file_path: str
    system: str = ""
    human: str = ""
    instruction: str = ""


class PromptUpdateRequest(BaseModel):
    version: str = Field(min_length=1, max_length=64)
    variables: list[str] = Field(default_factory=list)
    system: str = ""
    human: str = ""
    instruction: str = ""
