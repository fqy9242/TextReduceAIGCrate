from __future__ import annotations

import asyncio
import uuid

import pytest


async def _login(client, username: str, password: str) -> dict:
    resp = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_smoke_e2e_main_journey(client) -> None:
    admin = await _login(client, "admin", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    meta_resp = await client.get("/api/v1/prompts/metadata", headers=admin_headers)
    assert meta_resp.status_code == 200, meta_resp.text
    assert len(meta_resp.json()["items"]) >= 1

    reload_resp = await client.post("/api/v1/prompts/reload", headers=admin_headers)
    assert reload_resp.status_code == 200, reload_resp.text

    username = f"smoke_{uuid.uuid4().hex[:8]}"
    create_user = await client.post(
        "/api/v1/users",
        json={"username": username, "password": "Passw0rd!", "role": "operator"},
        headers=admin_headers,
    )
    assert create_user.status_code == 200, create_user.text
    user_id = create_user.json()["id"]

    role_update = await client.patch(
        f"/api/v1/users/{user_id}/role",
        json={"role": "operator"},
        headers=admin_headers,
    )
    assert role_update.status_code == 200

    operator = await _login(client, username, "Passw0rd!")
    operator_headers = {"Authorization": f"Bearer {operator['access_token']}"}

    create_task = await client.post(
        "/api/v1/tasks",
        json={
            "input_text": "冒烟测试流程中提交任务，验证从登录到改写结果导出的关键路径是否可用。"
            "文本需要保持含义不变，同时尽量降低 AIGC 检测分数。",
            "target_score": 20,
            "max_rounds": 3,
            "style": "deai_external",
        },
        headers=operator_headers,
    )
    assert create_task.status_code == 200, create_task.text
    task_id = create_task.json()["id"]

    final_status = None
    for _ in range(60):
        status_resp = await client.get(f"/api/v1/tasks/{task_id}", headers=operator_headers)
        assert status_resp.status_code == 200
        payload = status_resp.json()
        if payload["status"] in {"success", "not_met", "failed"}:
            final_status = payload["status"]
            break
        await asyncio.sleep(0.2)

    assert final_status in {"success", "not_met"}

    export_resp = await client.get(f"/api/v1/tasks/{task_id}/export", headers=operator_headers)
    assert export_resp.status_code == 200
    assert "Best Rewritten Text:" in export_resp.text
