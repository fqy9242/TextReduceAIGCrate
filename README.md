# Text AIGC Reducer

中文文本降 AIGC 率智能体应用（FastAPI + LangChain/LangGraph + Vue3）。

## 项目简介

系统围绕「改写 -> 检测 -> 决策」闭环运行，目标是在保证语义不变的前提下，降低文本 AIGC 检测分数。

当前策略固定为：
- `deai_external`（外部规则增强）

## 技术栈

后端：
- FastAPI
- SQLAlchemy + Alembic
- LangChain + LangGraph
- JWT 鉴权 + RBAC

前端：
- Vue 3 + Vite + TypeScript
- Pinia + Vue Router
- Element Plus

## 目录结构

```text
.
├─ backend/
│  ├─ app/                  # API、鉴权、RBAC、任务闭环
│  ├─ alembic/              # 迁移脚本
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/                  # 登录、工作台、任务、历史、管理中心
│  ├─ package.json
│  └─ .env.example
├─ prompts/zh-CN/           # Prompt YAML（统一管理，禁止硬编码）
├─ .external/               # 外部规则仓库（可选）
└─ run.bat                  # 一键安装/迁移/启动
```

## 核心能力

- 异步任务状态机：`queued/running/success/not_met/failed`
- 闭环节点：`load_prompt -> rewrite_with_llm -> detect_score -> decide_next -> persist_iteration`
- 达标规则：任一轮 `score <= target_score` 立即成功
- 未达标规则：达到最大轮次返回最低分版本并标记 `not_met`
- 检测适配器：`MockDetector`（默认）/ `HttpDetector`（可替换第三方）
- Prompt YAML 热重载（管理员）

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+

### 1) 准备环境变量

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

默认管理员（可在 `backend/.env` 修改）：
- 用户名：`admin`
- 密码：`Admin@123456`

### 2) 一键启动（推荐）

```powershell
.\run.bat
```

可选参数：

```powershell
.\run.bat --install
.\run.bat --no-start
.\run.bat --skip-migrate
```

启动后访问：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`

## 主要接口

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}/export`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{id}/role`
- `GET /api/v1/prompts/metadata`
- `POST /api/v1/prompts/reload`

## 测试

```powershell
cd backend
python -m pytest
```

## 常见问题

- 登录后无管理权限：检查 `admin` 是否仍绑定 `admin` 角色。
- 改写效果弱：确认 `USE_MOCK_LLM=auto/false`，并正确配置 `OPENAI_API_KEY`。
- 数据库连接失败：核对 `DATABASE_URL`/`SYNC_DATABASE_URL` 用户名密码及权限。
