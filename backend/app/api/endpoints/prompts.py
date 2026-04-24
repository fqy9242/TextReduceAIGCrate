from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.auth import MessageResponse
from app.schemas.prompt import PromptDetail, PromptMetadata, PromptMetadataResponse, PromptUpdateRequest
from app.services.rbac import (
    PERM_PROMPT_READ,
    PERM_PROMPT_RELOAD,
    PERM_PROMPT_WRITE,
    has_permission,
)


router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/metadata", response_model=PromptMetadataResponse)
async def get_prompt_metadata(
    request: Request,
    user: User = Depends(get_current_user),
) -> PromptMetadataResponse:
    role_names = [role.name for role in user.roles]
    if not has_permission(role_names, PERM_PROMPT_READ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to read prompts")

    prompt_manager = request.app.state.prompt_manager
    items = [
        PromptMetadata(
            group=item.group,
            name=item.name,
            version=item.version,
            variables=item.variables,
            file_path=item.file_path,
        )
        for item in prompt_manager.list_metadata()
    ]
    return PromptMetadataResponse(items=items)


@router.post("/reload", response_model=MessageResponse)
async def reload_prompts(
    request: Request,
    user: User = Depends(get_current_user),
) -> MessageResponse:
    role_names = [role.name for role in user.roles]
    if not has_permission(role_names, PERM_PROMPT_RELOAD):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to reload prompts")

    request.app.state.prompt_manager.reload()
    if hasattr(request.app.state, "external_rules_loader"):
        request.app.state.external_rules_loader.reload()
    return MessageResponse(message="Prompt definitions reloaded")


@router.get("/{group}/{name}", response_model=PromptDetail)
async def get_prompt_detail(
    group: str,
    name: str,
    request: Request,
    user: User = Depends(get_current_user),
) -> PromptDetail:
    role_names = [role.name for role in user.roles]
    if not has_permission(role_names, PERM_PROMPT_READ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to read prompts")

    prompt_manager = request.app.state.prompt_manager
    try:
        item = prompt_manager.get_prompt(group, name)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found") from exc

    return PromptDetail(
        group=item.group,
        name=item.name,
        version=item.version,
        variables=item.variables,
        file_path=item.file_path,
        system=item.system,
        human=item.human,
        instruction=item.instruction,
    )


@router.put("/{group}/{name}", response_model=MessageResponse)
async def update_prompt(
    group: str,
    name: str,
    payload: PromptUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
) -> MessageResponse:
    role_names = [role.name for role in user.roles]
    if not has_permission(role_names, PERM_PROMPT_WRITE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to write prompts")

    prompt_manager = request.app.state.prompt_manager
    try:
        prompt_manager.update_prompt(
            group=group,
            name=name,
            version=payload.version,
            variables=payload.variables,
            system=payload.system,
            human=payload.human,
            instruction=payload.instruction,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if hasattr(request.app.state, "external_rules_loader"):
        request.app.state.external_rules_loader.reload()
    return MessageResponse(message="Prompt updated")
