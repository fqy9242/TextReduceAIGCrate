from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.auth import MessageResponse
from app.schemas.prompt import PromptMetadata, PromptMetadataResponse
from app.services.rbac import PERM_PROMPT_READ, PERM_PROMPT_RELOAD, has_permission


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
