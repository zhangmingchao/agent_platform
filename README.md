# Agent Platform

基于 FastAPI、Vue 3、MySQL 和 CrewAI 的多智能体编排平台。平台将可复用 Agent、团队 Crew、任务 Task 和跨团队 Flow 分层管理，并为每轮执行保存会话与 Trace 调用链。

## 核心架构

```text
Flow（跨团队业务流程）
  └─ Crew（团队，sequential / hierarchical）
      ├─ Agent（可复用成员）
      │   ├─ Skill
      │   └─ MCP tools
      └─ Task（工作单元）
          ├─ 负责 Agent
          ├─ 前置 Task
          └─ Skill / MCP 任务级白名单
```

- **Agent**：定义 Role、Goal、Backstory、模型及可使用的 Skill/MCP。
- **Crew**：选择成员、执行方式和 Manager，并组织多个 Task。
- **Task**：定义任务描述、预期输出、负责人和依赖。Task 的 Skill/MCP 选择是白名单，不改变 Agent 的能力归属；某一类不选择时，允许负责人使用该类全部能力。
- **Flow**：数据库驱动的有向图执行器，可串联 Crew、条件、人工审批、转换和结束节点。
- **Trace**：每轮对话记录 Crew、Task、Flow 节点和工具调用的状态、输入输出及耗时。

更完整的设计和约束见 [docs/CREWAI_ARCHITECTURE.md](docs/CREWAI_ARCHITECTURE.md)。

## 功能

- JWT 登录、注册、修改密码
- Agent CRUD 和 CrewAI 能力参数
- Skill ZIP 包上传、文件树、Markdown 编辑与预览
- MCP Server 配置、工具发现与在线调试
- Crew 与 Task 可视化表单编排
- Flow 节点和条件连线编排
- Crew/Flow 会话隔离及 SSE 响应
- Trace 调用链查看
- 中英文 Dashboard

## 技术栈

- 后端：Python 3.11、FastAPI、CrewAI 1.15.15、aiomysql、PyJWT
- 前端：Vue 3、Vite、Element Plus、Pinia、Vue Router、Axios
- 数据库：本地 MySQL，默认 `127.0.0.1:3306/agent_platform`
- 模型：默认通过 OpenAI 兼容协议调用 DeepSeek

## 快速开始

### 1. 重建数据库

> 警告：`backend/sql/init.sql` 会 DROP 全部业务表和历史数据。

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p123456 < backend/sql/init.sql
```

默认账号：`admin / 123456`、`test / 123456`。

### 2. 后端

项目要求 Python 3.11。仓库已有 `.python-version`，推荐使用独立 CrewAI 环境：

```bash
python3.11 -m venv .venv-crewai
source .venv-crewai/bin/activate
pip install -r backend/requirements.txt
export DEEPSEEK_API_KEY="your-api-key"
python -m backend.main
```

后端及构建后的前端地址：`http://127.0.0.1:20000`。

### 3. 前端开发

```bash
cd frontend
npm install
npm run dev
```

开发地址：`http://127.0.0.1:20001`，`/api` 代理到 `127.0.0.1:20000`。

### 4. 前端生产构建

```bash
cd frontend
npm run build
```

构建文件位于 `frontend/dist`，后端会自动提供静态页面。

## 推荐使用顺序

1. 创建 Skill 和 MCP 配置。
2. 创建 Agent，填写 Role、Goal、Backstory，并挂载 Skill/MCP。
3. 创建 Crew，选择成员与执行方式，再配置 Task、负责人和依赖。
4. 需要跨 Crew 流程时创建 Flow，配置节点与连线。
5. 在 Crew 或 Flow 列表点击“运行”进入对话。
6. 在 Trace 页面查看本轮调用链。

## 执行方式

- `sequential`：Task 按顺序执行，每个 Task 必须指定负责 Agent。
- `hierarchical`：Manager Agent 负责协调和委派，Crew 至少还需一个协作 Agent；Task 可以不指定负责人，也可以指定非 Manager 成员。

`Planning`、`Memory` 可能使用额外模型或向量能力，默认关闭。启用前请确认所使用模型与 embedding 配置可用。

## Flow 节点

| 类型 | 行为 |
|---|---|
| `crew` | 执行指定 Crew，并把结果作为后续状态 |
| `condition` | 不改变状态，由出边条件选择下一节点 |
| `transform` | 按配置中的 `prefix`、`suffix` 转换文本 |
| `approval` | 返回“等待人工审批”并停止本轮执行 |
| `end` | 结束流程并返回当前状态 |

出边支持 `always`、`contains`、`equals`、`not_contains`，数字较小的优先级先匹配。当前审批节点尚无恢复 API，需要用户发起新一轮执行。

## 主要 API

| 模块 | 接口 |
|---|---|
| Agent | `GET/POST /api/agents`、`GET/PUT/DELETE /api/agents/{id}`；列表兼容接口为 `/api/agentsList` |
| Crew | `GET/POST /api/crews`、`GET/PUT/DELETE /api/crews/{id}` |
| Flow | `GET/POST /api/flows`、`GET/PUT/DELETE /api/flows/{id}` |
| Skill | `/api/skills`、`/api/skills/upload`、`/api/skills/{id}/files` |
| MCP | `/api/mcp-configs`、`/api/mcp-configs/{id}/tools`、`/api/mcp-configs/{id}/call` |
| 会话 | `GET/POST /api/sessions`，使用 `target_type=crew|flow` 与 `target_id` |
| 对话 | `POST /api/chat/stream`，请求体 `{"session_id": 1, "message": "你好"}` |
| Trace | `GET /api/traces`、`GET /api/traces/{id}` |

## 数据库表

```text
users
agents ── agent_skills ── skills
       └─ agent_mcps   ── mcp_configs
crews ── crew_agents
      └─ crew_tasks ── task_dependencies
                    ├─ task_skills
                    └─ task_mcps
flows ── flow_nodes ── flow_edges
chat_sessions ── chat_messages
              └─ trace_runs ── trace_spans
```

运行时 `database.py` 只做非破坏性的 `CREATE TABLE IF NOT EXISTS`，结构性升级应使用 `backend/sql/init.sql` 或正式迁移脚本。

## 环境变量

| 变量 | 默认值 |
|---|---|
| `DEEPSEEK_API_KEY` | 空（真实执行必填） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `JWT_SECRET` | `agent-platform-secret-2026-change-me-now` |
| `SERVER_PORT` | `20000` |
| `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` |
| `DB_USER` / `DB_PASSWORD` | `root` / `123456` |
| `DB_NAME` | `agent_platform` |

## Skill 包

上传格式为 ZIP，包内必须包含 `SKILL.md`，可同时包含 `references/` 等目录：

```text
my-skill.zip
├── SKILL.md
└── references/
    └── guide.md
```

文件解压到 `backend/data/skills/{skill_id}/`；数据库 `skills.content` 保存入口内容快照。
