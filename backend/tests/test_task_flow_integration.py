from __future__ import annotations

import asyncio
import uuid

import pytest


async def _login(client, username: str, password: str) -> dict:
    response = await client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_task_flow_create_poll_export(client) -> None:
    admin = await _login(client, "admin", "Admin@123456")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    operator_name = f"operator_{uuid.uuid4().hex[:8]}"
    create_user = await client.post(
        "/api/v1/users",
        json={"username": operator_name, "password": "Passw0rd!", "role": "operator"},
        headers=admin_headers,
    )
    assert create_user.status_code == 200, create_user.text

    operator = await _login(client, operator_name, "Passw0rd!")
    operator_headers = {"Authorization": f"Bearer {operator['access_token']}"}

    create_task = await client.post(
        "/api/v1/tasks",
        json={
            "input_text": "为了验证系统端到端任务流程，这里提供一段足够长度的中文文本。"
            "我们希望系统能够在多轮改写后逐步降低检测分数，并最终返回最优版本。"
            "该流程还需要保证语义不变与可读性平衡。",
            "target_score": 20,
            "max_rounds": 3,
            "style": "deai_external",
        },
        headers=operator_headers,
    )
    assert create_task.status_code == 200, create_task.text
    task_id = create_task.json()["id"]

    final_payload = None
    for _ in range(60):
        task_resp = await client.get(f"/api/v1/tasks/{task_id}", headers=operator_headers)
        assert task_resp.status_code == 200
        payload = task_resp.json()
        if payload["status"] in {"success", "not_met", "failed"}:
            final_payload = payload
            break
        await asyncio.sleep(0.2)

    assert final_payload is not None
    assert final_payload["status"] in {"success", "not_met"}
    assert final_payload["rounds_used"] >= 1
    assert len(final_payload["iterations"]) >= 1

    export_resp = await client.get(f"/api/v1/tasks/{task_id}/export", headers=operator_headers)
    assert export_resp.status_code == 200
    assert f"Task ID: {task_id}" in export_resp.text
