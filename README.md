# Text AIGC Reducer

**基于AI, 使用AI来降低论文/文本AI率, 用魔法来打败魔法**

多轮迭代: 改写智能体改写第一版 => 评分智能体进行评分 => 低于预期分数将会继续进行多轮改写 => 否则直接保留最优版本

目前版本: 仅支持自选文字进行改写 注意不要复制整篇论文来进行改写 否则由于上下文限制等 模型可能会异常返回!

![image-20260427151459135](https://q-gallery.oss-cn-guangzhou.aliyuncs.com/img/202604271514253.png)

![image-20260427151507729](https://q-gallery.oss-cn-guangzhou.aliyuncs.com/img/202604271515042.png)

![image-20260427151431832](https://q-gallery.oss-cn-guangzhou.aliyuncs.com/img/202604271514086.png)

![image-20260427151409658](https://q-gallery.oss-cn-guangzhou.aliyuncs.com/img/202604271514868.png)

![image-20260427151330198](https://q-gallery.oss-cn-guangzhou.aliyuncs.com/img/202604271513485.png)

## Why This Project

很多“降 AIGC”工具只有单次改写，没有任务追踪、参数管理和结果复盘能力。这个项目把改写流程做成了可观测、可配置、可复盘的完整应用，适合：

- 需要批量或持续处理中文文本的场景
- 需要保留任务历史、迭代轨迹和日志记录的团队
- 想在本地二次开发 Prompt、策略和检测链路的开发者

## Features

- 闭环任务流：`rewrite -> detect -> decide -> persist`
- 任务状态机：`queued / running / success / not_met / failed / cancelled`
- 多 worker 并发执行队列，支持活动任务看板
- Prompt YAML 在线管理，避免把 Prompt 硬编码进代码
- 系统设置在线管理，包括默认任务参数和 LLM 非敏感运行参数
- RBAC 权限控制，支持登录、刷新、用户管理和角色分配
- 历史任务追踪、任务导出、任务取消、重试与日志查看

## Tech Stack

后端：
- FastAPI
- SQLAlchemy 2 + Alembic
- LangChain + LangGraph
- JWT + RBAC
- SQLite / MySQL

前端：
- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus

## Project Structure

```text
.
├─ backend/
│  ├─ app/                  # API、服务层、鉴权、RBAC、任务闭环
│  ├─ alembic/              # 数据库迁移
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/                  # 页面、布局、状态管理、API 封装
│  ├─ package.json
│  └─ .env.example
├─ prompts/zh-CN/           # Prompt YAML
├─ run.bat                  # Windows 一键安装/迁移/启动
├─ LICENSE
└─ README.md
```

## Quick Start

### Requirements

- Python 3.9+
- Node.js 18+

### 1. Clone

```powershell
git clone git@github.com:fqy9242/TextReduceAIGCrate.git
cd TextReduceAIGCrate
```

### 2. Prepare Environment Files

```powershell
cp backend\.env.example backend\.env
cp frontend\.env.example frontend\.env
```

`backend/.env` 主要保存两类配置：
- 敏感配置，例如 `OPENAI_API_KEY`、`SECRET_KEY`
- 基础设施配置，例如数据库连接、鉴权时长、任务超时、并发 worker 数

默认管理员账号（首次启动后可修改）：
- 用户名：`admin`
- 密码：`Admin@123456`

### 3. One-Command Startup

#### windows OS

```powershell
.\run.bat
```

可选参数：

```powershell
.\run.bat --install
.\run.bat --no-start
.\run.bat --skip-migrate
```

启动后默认地址：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- OpenAPI：`http://localhost:8000/docs`

### 4. Configure Runtime Settings

首次登录后，进入“管理中心 -> 系统设置”配置：
- 默认目标分数
- 默认最大轮次
- 默认策略
- `openai_base_url`
- `openai_model`
- `openai_timeout_seconds`
- `openai_max_retries`

说明：
- `OPENAI_API_KEY` 仍然只从 `backend/.env` 读取
- 队列并发度通过 `TASK_WORKER_CONCURRENCY` 配置

## Development

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
$env:PYTHONPATH=(Get-Location).Path
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Database Migration

```powershell
cd backend
python -m alembic upgrade head
```

### Test and Build

后端测试：

```powershell
cd backend
python -m pytest
```

前端构建：

```powershell
cd frontend
npm run build
```

## Contributing

欢迎提交 Issue 和 Pull Request。

### Contribution Workflow

1. Fork 仓库并克隆到本地

```powershell
git clone git@github.com:<your-account>/TextReduceAIGCrate.git
cd TextReduceAIGCrate
```

2. 创建功能分支

```powershell
git checkout -b feat/your-change
```

3. 安装依赖并跑起本地环境

```powershell
.\run.bat --install
```

4. 编写代码并自测

建议至少完成：
- 后端相关改动：`cd backend && python -m pytest`
- 前端相关改动：`cd frontend && npm run build`
- 涉及界面变化时，附上截图或录屏
- 涉及数据库结构变化时，附上 Alembic migration

5. 提交变更

推荐使用清晰的提交前缀：
- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`
- `chore:`

示例：

```text
feat: improve workspace task board refresh logic
fix: handle cancelled task state in dashboard
docs: rewrite README for open source contributors
```

6. 发起 Pull Request

建议在 PR 描述里写清楚：
- 改动目的
- 改动范围
- 测试方式
- 是否包含迁移、配置变更或破坏性变更

### Contribution Notes

提交代码时请注意：

- 不要把 API Key、数据库密码等敏感信息提交进仓库
- Prompt 统一放在 `prompts/zh-CN/`，不要硬编码到业务代码里
- 尽量补测试，尤其是任务流、权限和配置相关逻辑
- 如果修改了 API、配置项或行为约定，请同步更新 README

## Roadmap

欢迎围绕以下方向继续演进：

- 更强的检测器适配层
- 更细粒度的任务调度与限流
- 更完善的任务批处理能力
- 更清晰的多策略对比与评估结果展示
- 更标准的 CI、Issue Template 和 PR Template

## FAQ

- 登录后没有管理权限：
  检查 `admin` 是否仍绑定 `admin` 角色。
- 任务执行失败：
  优先检查 `OPENAI_API_KEY`、`openai_base_url`、`openai_model` 和超时配置。
- 数据库连接失败：
  检查 `DATABASE_URL` / `SYNC_DATABASE_URL`、用户权限和驱动配置。

## License

本项目采用 GNU General Public License v3.0 许可协议发布，详见 [LICENSE](./LICENSE)。
