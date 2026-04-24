from __future__ import annotations

from typing import Iterable


PERM_TASK_CREATE = "task:create"
PERM_TASK_READ_OWN = "task:read_own"
PERM_TASK_READ_ALL = "task:read_all"
PERM_TASK_EXPORT_OWN = "task:export_own"
PERM_TASK_EXPORT_ALL = "task:export_all"
PERM_USER_MANAGE = "user:manage"
PERM_PROMPT_READ = "prompt:read"
PERM_PROMPT_RELOAD = "prompt:reload"


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        PERM_TASK_CREATE,
        PERM_TASK_READ_OWN,
        PERM_TASK_READ_ALL,
        PERM_TASK_EXPORT_OWN,
        PERM_TASK_EXPORT_ALL,
        PERM_USER_MANAGE,
        PERM_PROMPT_READ,
        PERM_PROMPT_RELOAD,
    },
    "operator": {
        PERM_TASK_CREATE,
        PERM_TASK_READ_OWN,
        PERM_TASK_EXPORT_OWN,
        PERM_PROMPT_READ,
    },
    "viewer": {
        PERM_TASK_READ_OWN,
        PERM_TASK_EXPORT_OWN,
        PERM_PROMPT_READ,
    },
}


def has_permission(role_names: Iterable[str], permission: str) -> bool:
    effective_permissions: set[str] = set()
    for role in role_names:
        effective_permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permission in effective_permissions

