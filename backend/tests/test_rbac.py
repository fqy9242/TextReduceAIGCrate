from __future__ import annotations

from app.services.rbac import (
    PERM_PROMPT_RELOAD,
    PERM_TASK_CREATE,
    PERM_TASK_READ_OWN,
    PERM_USER_MANAGE,
    has_permission,
)


def test_rbac_admin_has_manage_permission() -> None:
    assert has_permission(["admin"], PERM_USER_MANAGE)
    assert has_permission(["admin"], PERM_PROMPT_RELOAD)


def test_rbac_operator_cannot_manage_users() -> None:
    assert has_permission(["operator"], PERM_TASK_CREATE)
    assert has_permission(["operator"], PERM_TASK_READ_OWN)
    assert not has_permission(["operator"], PERM_USER_MANAGE)

