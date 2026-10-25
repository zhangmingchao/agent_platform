# Agent Platform

一个完整的 AI Agent 管理平台，支持：
- 🔐 **用户登录/注册** - JWT 认证
- 🤖 **Agent 管理** - 创建、编辑、删除 Agent，配置系统提示词、模型、温度和工具迭代次数
- 📝 **Skill 管理** - 上传 ZIP 技能包（`SKILL.md` + `references/`），在线编辑与 Markdown 预览
- 🔌 **MCP 配置** - 配置多个 MCP Server，动态发现、查看和调试工具
- 💬 **流式对话** - SSE 流式响应，多轮 Tool Call 自动循环
- ⏱️ **执行控制** - Agent 整体超时、MCP 操作超时与用户主动停止
- 🧩 **插件化 LLM Adapter** - 通过统一适配器注册表接入 OpenAI、DeepSeek、Qwen 或兼容网关
- 🛡️ **权限预设** - 按 Agent 配置安全、标准、自动和开发者模式，统一控制工具沙箱边界
- 🔁 **Agent Loop 生命周期** - 流式执行过程中输出 turn、step、LLM 和 tool 阶段事件
- 📋 **显式任务规划** - 可选地先生成有限步骤，再按顺序执行并汇总结果
- 📊 **BI 元数据 CLI** - 通过受控只读命令查询分析主体、事件、属性和指标
- 🔑 **外部 Agent API** - 用户 API Key 鉴权，调用方自行维护聊天历史
- 🔎 **Trace 调用链** - 记录每次对话的 LLM 轮次、工具调用、输入输出、错误与耗时
- 📱 **Web UI** - Vue 3 + Element Plus 前端

## 目录结构

```
agent_platform/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── runtime_worker.py    # 独立 Python Runtime Worker 入口
│   ├── plugin_worker.py     # Python 插件安装与执行 Worker 入口
│   ├── routers/             # HTTP 接口路由
│   │   ├── auth.py
│   │   ├── agents.py
│   │   ├── skills.py
│   │   ├── mcp_configs.py
│   │   ├── sessions.py
│   │   ├── chat.py
│   │   └── traces.py
│   ├── services/            # 业务服务层
│   │   ├── agent_service.py
│   │   ├── skill_service.py
│   │   ├── mcp_config_service.py
│   │   └── trace_service.py
│   ├── config.py            # 配置（端口、密钥、MySQL 连接）
│   ├── database.py          # MySQL 数据库层（aiomysql）
│   ├── auth.py              # JWT 认证
│   ├── mcp_client.py        # MCP 客户端（Streamable HTTP）
│   ├── chat_engine.py       # 流式对话核心（多轮 Tool Call）
│   ├── requirements.txt     # Python 依赖
│   ├── sql/init.sql         # MySQL 非破坏性初始化脚本
│   └── data/skills/{id}/    # 解压后的 Skill 包（SKILL.md、references 等）
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 布局组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── router/          # Vue Router
│   │   └── utils/           # 工具函数
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 技术栈

### 后端
| 技术 | 用途 |
|---|---|
| FastAPI | Web 框架 |
| Uvicorn | ASGI 服务器 |
| aiomysql | 异步 MySQL |
| Redis Stream | 工作流事件存储与 SSE 实时订阅 |
| PyJWT | JWT 认证 |
| LangChain / LangGraph | Agent、工具调用与工作流执行 |
| Redis Checkpointer | 工作流 State、人工审批暂停与跨进程恢复 |
| HTTPX | MCP 通信 |

### 前端
| 技术 | 用途 |
|---|---|
| Vue 3 | 前端框架 |
| Vite | 构建工具 |
| Element Plus | UI 组件库 |
| Pinia | 状态管理 |
| Vue Router | 路由 |
| Axios | HTTP 客户端 |
| markdown-it + DOMPurify | Markdown 渲染与安全过滤 |

## 快速开始

### 0. 启动 Redis Stack

工作流持久化 Checkpoint 需要 RedisJSON 和 RediSearch。项目提供了启用 AOF 的 Redis
Stack 配置：

```bash
docker compose -f docker-compose.redis.yml up -d
```

如果仍使用普通 Redis，应用会回退到内存 Checkpoint，并在日志中提示跨进程恢复不可用。

### 1. 后端启动

```bash
cd agent_platform
pip install -r backend/requirements.txt

# 配置环境变量（可选）
export DEEPSEEK_API_KEY="your-api-key"
export DEEPSEEK_MODEL="deepseek-chat"
export JWT_SECRET="your-secret"
export MODEL_API_KEY_ENCRYPTION_KEY="请填写32字节随机密钥的URL-safe Base64"
export SERVER_PORT="20000"

# 配置 MySQL 连接（可选，默认值如下）
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD="123456"
export DB_NAME="agent_platform_langchain"

# 启动服务（首次启动会自动创建数据库、表结构和必要字段）
python -m backend.main
```

### BI、JSON 与 Python 进程插件

两个内置插件均需要安装到当前用户的 Runtime Docker 容器：在「插件管理」点击安装，等待已就绪，然后配置、启用并绑定 Agent。JSON 无需配置；BI 需填写容器可达的服务地址和 Token，配套 Skill 随安装版本加载。

工具名分别为 `plugin__bi_metadata__BiCli` 和 `plugin__json_tools__JsonFormat`。Agent 不再通过全局 `BI_CLI_ENABLED` 环境配置自动获得 BI 工具。`backend.bi_cli` 保留为可手动使用的只读 CLI 库，其环境配置不用于 Agent 插件执行。

启用 Python Runtime 时，需要在另一个终端启动独立 Worker：

```bash
cd agent_platform

# 先启动 Docker Desktop，再构建沙箱镜像和常驻 Sandbox Manager
export SANDBOX_SERVICE_TOKEN="请替换为随机内部密钥"
docker compose -f docker-compose.sandbox.yml up -d --build

# Sandbox Service 健康检查
curl -H "Authorization: Bearer $SANDBOX_SERVICE_TOKEN" http://127.0.0.1:20002/health

# 启动 Redis 队列消费者
python -m backend.runtime_worker

# 使用内置或上传 Python 插件时，另外启动插件任务消费者（单独终端）
python -m backend.plugin_worker
```

API 进程只负责准备任务并写入 Redis 队列；`runtime_worker` 负责启动受限 Python
代码任务，独立 `sandbox-service` 负责在用户私有 Docker 容器中执行代码、收集日志
和登记生成文件。未启动 Worker 或 Sandbox Service 时，`ExecutePython` 会在等待超时后
返回明确错误。单个 Worker 同时执行一个任务，可以启动多个 Worker 进程增加本机并发度。

插件上传、导出、版本切换和 Agent 绑定见 [插件文档](docs/plugins.md)。内置和上传代码均通过
`plugin_worker` 在用户现有 Runtime 容器中安装依赖、按次启动进程；插件队列直接存储
在 MySQL，Runtime 继续使用 Redis 队列。API、两个 Worker 必须使用相同的数据库、
数据目录、加密主密钥、`SANDBOX_SERVICE_URL` 和内部 Token。IDE 启动请选择模块
`backend.plugin_worker` / `backend.runtime_worker`，工作目录设为项目根目录。

后端启动后：
- API 地址: `http://127.0.0.1:20000`
- 首次使用请通过注册页面创建账号；系统不再创建默认弱口令账号
- 数据库: MySQL（默认使用 `agent_platform_langchain` 数据库）

后端启动时会自动创建数据库和表结构。也可以在首次启动前手动初始化：

```bash
mysql -u root -p < backend/sql/init.sql
```

`init.sql` 使用 `CREATE TABLE IF NOT EXISTS`，不会主动删除已有表或数据；现有数据库的版本升级仍由后端启动迁移逻辑处理。

### 2. 前端开发

```bash
cd agent_platform/frontend
npm install
npm run dev
```

前端开发服务器: `http://127.0.0.1:20001`（自动代理 `/api` 到后端 20000 端口）

### 3. 生产部署

```bash
# 构建前端
cd agent_platform/frontend
npm run build

# 启动后端（已包含前端静态文件服务）
cd ..
python -m backend.main
```

访问 `http://127.0.0.1:20000` 即可使用完整系统。

## API 接口

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/register` | 注册 |
| GET | `/api/auth/me` | 当前用户信息 |
| PUT | `/api/auth/password` | 修改当前用户密码 |
| POST | `/api/auth/logout` | 登出 |

### Agent
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/agentsList` | Agent 列表 |
| GET | `/api/agents/{id}` | Agent 详情 |
| POST | `/api/agents` | 创建 Agent |
| PUT | `/api/agents/{id}` | 更新 Agent |
| DELETE | `/api/agents/{id}` | 删除 Agent |
| GET | `/api/ll_models` | 可用模型列表 |

### 模型配置
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/models/adapters` | 查看后端已注册的 LLM Adapter |
| GET | `/api/modelsList` | 当前用户的模型配置列表 |
| POST | `/api/models` | 创建模型配置 |
| PUT | `/api/models/{id}` | 更新模型配置 |
| DELETE | `/api/models/{id}` | 删除模型配置 |
| POST | `/api/models/{id}/test` | 测试已保存模型连接 |
| POST | `/api/models/test` | 测试未保存模型配置 |

### Skill
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/skills` | Skill 列表 |
| GET | `/api/skills/{id}` | Skill 详情 |
| PUT | `/api/skills/{id}` | 更新名称和描述 |
| POST | `/api/skills/upload` | 上传 ZIP 技能包 |
| POST | `/api/skills` | 手动创建 Skill |
| GET | `/api/skills/{id}/files` | 技能包文件列表 |
| GET | `/api/skills/{id}/files/{path}` | 读取技能包文本文件 |
| PUT | `/api/skills/{id}/files/{path}` | 更新技能包文本文件 |
| DELETE | `/api/skills/{id}` | 删除 Skill |

### MCP 配置
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/mcp-configs` | MCP 配置列表 |
| POST | `/api/mcp-configs` | 创建 MCP 配置 |
| PUT | `/api/mcp-configs/{id}` | 更新 MCP 配置 |
| DELETE | `/api/mcp-configs/{id}` | 删除 MCP 配置 |
| GET | `/api/mcp-configs/{id}/tools` | 发现 MCP 工具 |
| POST | `/api/mcp-configs/{id}/call` | 调试调用 MCP 工具 |

每个 MCP Server 可以独立设置 `1-60` 秒的操作超时，默认 `30` 秒。该时限覆盖一次
完整的初始化、工具发现或工具调用，而不是只限制其中某一个 HTTP 请求。

### 会话 & 对话
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/sessions?agent_id={id}` | 按当前用户与 Agent 查询会话 |
| POST | `/api/sessions` | 创建会话 |
| PUT | `/api/sessions/{id}` | 重命名会话 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/sessions/{id}/messages` | 历史消息 |
| POST | `/api/chat/stream` | SSE 流式对话（JSON 请求体） |

### 外部 Agent API
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/api-key` | 查询当前登录用户的脱敏 API Key 状态 |
| POST | `/api/api-key` | 创建或轮换 API Key，完整密钥只返回一次 |
| DELETE | `/api/api-key` | 吊销当前用户的 API Key |
| POST | `/api/v1/agents/{id}/chat/stream` | 使用 `X-API-Key` 和调用方历史进行无状态 SSE 对话 |

外部聊天不接收平台 `session_id`，也不会写入 `chat_sessions` 或 `chat_messages`。
调用方必须在每次请求中提交完整的 `user/assistant` 消息历史。详细协议见
[`docs/external-chat-api.md`](docs/external-chat-api.md)。

### 插件化 LLM Adapter

模型调用不再由 Agent 工厂直接绑定 `ChatOpenAI`，而是先根据模型配置中的
`provider` 从 LLM Adapter 注册表选择适配器，再由适配器构建 LangChain Chat Model。
当前内置 `openai`、`deepseek`、`qwen` 三个供应商，它们都复用 OpenAI 兼容协议实现。

未知 `provider` 会回退为 OpenAI 兼容网关适配器，因此只要第三方或本地网关提供
OpenAI 风格的 `base_url`、`api_key` 和模型 ID，就可以先不改核心 Agent Loop 直接接入。
如果后续要支持非 OpenAI 协议，只需要新增一个实现 `LlmAdapter` 接口的类，并在
`backend/llm_adapters/registry.py` 注册即可。

每个 Adapter 会声明能力矩阵，包含流式输出、工具调用、视觉输入、JSON Schema、
Token usage、流式 usage、reasoning 参数、最大上下文长度、默认超时和默认重试次数。
这些能力可通过 `/api/models/adapters` 查询，后续 Agent 创建、模型测试和 SDK 可以用它
做兼容性校验。

### 显式任务规划

Agent 的“任务规划”默认关闭。开启后，普通平台聊天和外部 Agent API 会先把本轮目标
拆成最多 6 个顺序步骤，再让现有 ReAct Agent 逐步执行，最后由模型统一生成一次正式
回答。规划、步骤状态、结果和错误会关联到本次 Trace 持久化，并在聊天页及 Trace 详情中展示。

规划模型生成的原始 JSON 不会进入聊天正文。客户端断开、模型异常、结构化输出校验失败
或空响应时，活动计划会自动标记失败，未开始步骤会标记为跳过。多 Agent 工作流已经具备
显式节点编排，因此不会在工作流节点内部再次嵌套任务规划。

### Agent 执行超时与取消

每个 Agent 可以设置 `10-1800` 秒的整体执行超时，默认 `120` 秒。计时范围从 Agent
事件流开始到最终结果完成，包含显式规划、全部模型轮次、工具调用和最终汇总。系统不再
为单次模型调用设置一套独立时限；如果某次模型调用一直没有返回，仍会在 Agent 整体期限
用尽时被终止。工作流不设置额外的全局期限，只对其中每个 Agent 节点应用该配置。

### Agent 权限预设

每个 Agent 可以配置默认工具权限预设：

| 预设 | 沙箱模式 | 审批策略 | 说明 |
|---|---|---|---|
| `safe` | `read_only` | `never` | 安全模式，只允许低风险只读工具，中高风险工具直接拒绝。 |
| `standard` | `workspace_write` | `ask` | 标准模式，允许工作区内写入；高风险工具需要审批。 |
| `auto` | `workspace_write` | `never` | 自动模式，适合外部 API 和无人值守任务；高风险工具直接拒绝。 |
| `developer` | `full_access` | `ask` | 开发者模式，预留更宽执行边界；高风险工具仍需要审批。 |

当前版本已将 `ExecutePython` 接入权限网关。工具返回值会附带 `permission`
审计信息，包含本次权限预设、风险等级、沙箱模式、审批策略和拒绝原因。
所有 LangChain 工具会先经过 Tool Execution Pipeline，再进入真实 Skill、Runtime
或 MCP 执行逻辑；未识别工具默认按低风险处理，高风险关键字工具会默认要求审批。

权限预设内部已展开为细粒度规则快照，包含工具允许/拒绝列表、可读路径、可写路径、
网络策略、允许域名和阻断命令关键字。当前版本先将这些规则用于权限决策和审计记录；
路径、网络和命令规则会随后继续下沉到 Runtime 容器与 Shell 类工具的强制执行层。

### Tool Execution Pipeline

所有 LangChain 工具执行前都会经过统一流水线：

| 阶段 | 说明 |
|---|---|
| `validate_arguments` | 标准化参数并生成参数摘要。 |
| `permission_decision` | 根据权限预设、工具风险和细粒度规则生成允许或拒绝决策。 |
| `before_execute` | 记录沙箱模式等执行前上下文。 |
| `execute` | 调用真实 Skill、Runtime 或 MCP 工具。 |
| `after_execute` | 记录耗时、结果类型并合并权限审计信息。 |
| `on_error` | 将异常标准化为事件，随后继续抛给原有调用链处理。 |

Pipeline 阶段事件会追加写入 `session_events`，不替代现有 Trace Span，而是作为更细的
执行时间线和调试数据。

### Agent Loop 生命周期

平台聊天流会输出 `agent_loop_event` SSE 事件，用于描述一次 Agent 执行从开始到结束的
稳定阶段。该事件不进入聊天正文，前端可以选择忽略，也可以用于后续的执行时间线、Trace
可视化或调试面板。

这些生命周期事件也会追加写入 `session_events`。事件日志采用 append-only 模式，不更新
历史事件；当前状态由事件序列推导，便于后续做执行回放、Trace 可视化和 Agent 调试面板。

聊天页已内置当前运行态观察面板，包含：

- 执行时间线：按事件到达顺序展示本轮 turn、step、LLM 和 tool 阶段。
- Trace 可视化：按 `step_id` 将 LLM 与 Tool 事件分组。
- Agent 调试面板：展示当前 phase、step、tool、turn 和 run 标识。

观察面板只消费当前 SSE 流，不回放历史数据；切换会话、创建新会话或发送新消息时会清空。

当前生命周期阶段包括：

| 阶段 | 说明 |
|---|---|
| `turn/start` | 一次用户请求开始。 |
| `step/start` | 一次模型步骤开始。 |
| `llm/start` | 模型调用开始。 |
| `llm/end` | 模型调用结束。 |
| `tool/start` | 工具调用开始。 |
| `tool/end` | 工具调用结束。 |
| `step/end` | 当前模型步骤结束。 |
| `turn/end` | 本轮用户请求正常完成。 |
| `turn/error` | 本轮用户请求异常结束。 |
| `turn/timeout` | 本轮用户请求达到整体超时。 |

事件结构示例：

```json
{
  "type": "agent_loop_event",
  "phase": "tool/start",
  "turn_id": "session_1_message_2",
  "step_id": "session_1_message_2:step-1",
  "step_no": 1,
  "run_id": "tool-run-id",
  "name": "ExecutePython"
}
```

平台聊天的“停止生成”通过中断当前 HTTP 流取消执行，外部调用方也可以主动关闭 SSE
连接。用户中断记录为 `cancelled`，系统达到 Agent 整体时限记录为 `timeout`。

### 多 Agent 工作流
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/workflows` | 工作流列表 |
| POST | `/api/workflows` | 创建工作流 |
| GET | `/api/workflows/{id}` | 工作流详情 |
| PUT | `/api/workflows/{id}` | 更新工作流 |
| DELETE | `/api/workflows/{id}` | 删除工作流 |
| POST | `/api/workflows/{id}/run` | 运行工作流 |
| GET | `/api/workflows/{id}/runs` | 工作流运行记录 |
| GET | `/api/workflows/runs/{run_id}` | 运行详情与步骤输出 |
| GET | `/api/workflows/runs/{run_id}/events` | 订阅 Redis Stream 工作流事件（SSE） |

### Trace 调用链
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/traces` | 当前用户的 Trace 列表 |
| GET | `/api/traces/{id}` | Trace 详情与 Span 调用链 |
| GET | `/api/traces/{id}/events` | Trace 关联的 append-only Session 事件 |

## 使用流程

1. **注册/登录** → 进入仪表盘
2. **创建 Skill** → 上传包含 `SKILL.md` 的 ZIP 技能包，或手动创建
3. **配置 MCP** → 添加 MCP Server，查看工具并通过 JSON 参数调试调用
4. **创建 Agent** → 设置名称、系统提示词、最大迭代次数，并关联 Skill 和 MCP
5. **开始对话** → 选择 Agent 创建会话，开始流式对话
6. **创建多 Agent 工作流** → 将多个 Agent 编排为顺序执行步骤
7. **查看 Trace** → 在 Trace 调用链菜单查看每轮 LLM 和工具调用详情

多 Agent 工作流示例：

```json
{
  "name": "需求分析与审查",
  "description": "先分析需求，再审查输出",
  "config": {
    "mode": "sequential",
    "steps": [
      {
        "agent_id": 1,
        "role": "需求分析师",
        "instruction": "分析用户需求，输出结构化实施方案。"
      },
      {
        "agent_id": 2,
        "role": "审查员",
        "instruction": "审查上一位 Agent 的方案，指出风险并给出最终建议。"
      }
    ]
  }
}
```

## 数据库结构

```
users          用户表（id, username, password, created_at）
models         模型配置表（provider, model_id, api_key, base_url, temperature, max_tokens）
agents         Agent 表（含模型、提示词、iteration_count、execution_timeout_seconds、planning_mode）
skills         Skill 表（id, user_id, name, description, content）
mcp_configs    MCP 配置表（含地址、端点、timeout_seconds、描述）
agent_skills   Agent-Skill 关联表（agent_id, skill_id）
agent_mcps     Agent-MCP 关联表（agent_id, mcp_id）
chat_sessions  会话表（id, user_id, agent_id, title）
chat_messages  消息表（id, session_id, role, content）
session_events  Session append-only 事件日志（Agent Loop、Pipeline、权限决策）
trace_runs     对话/工作流 Trace（含 workflow_run_id、workflow_step_id、状态与耗时）
trace_spans    Trace 节点（run_id、span_type、输入输出、错误、Token 与耗时）
agent_task_plans       Agent 显式任务计划（目标、状态、当前步骤、Trace 关联）
agent_task_plan_steps  任务计划步骤（指令、状态、结果与错误）
multi_agent_workflows  多 Agent 工作流配置（顺序或 DAG）
multi_agent_runs       多 Agent 工作流运行状态与最终结果
multi_agent_run_steps  工作流节点执行记录与 Trace 关联
```

`agents.iteration_count` 表示单次对话允许的最大工具调用迭代次数，取值范围为 `1–100`，
默认值为 `6`；`agents.execution_timeout_seconds` 表示 Agent 整体执行时限，取值范围为
`10-1800` 秒，默认值为 `120`。后端启动时会自动创建缺失的表，并补充当前版本需要的兼容字段。

## Skill 包格式

上传文件必须是 ZIP，解压后必须包含 `SKILL.md`。ZIP 可以直接包含文件，也可以包含一层外部目录；后端会自动去掉统一的外层目录。

```text
my-skill.zip
├── SKILL.md
├── skill.json              # 可选：声明 HTTP Action 工具
└── references/
    ├── guide.md
    └── example.json
```

- 文件解压到 `backend/data/skills/{skill_id}/`。
- 页面支持查看和编辑 UTF-8 文本文件，单文件上限为 1 MB。
- `.md` 文件支持编辑、实时预览和分栏模式。
- `SKILL.md` 是运行时指令主数据源；数据库 `skills.content` 保留兼容快照。
- `skill.json` 可选，用于声明可执行 HTTP Action。没有该文件时，Skill 仍按提示词/资料包模式运行。
- ZIP 最多包含 200 个有效文件，解压总大小不能超过 20 MB。

`skill.json` 示例：

```json
{
  "tools": [
    {
      "name": "query_weather",
      "description": "查询指定城市的天气",
      "type": "http",
      "method": "GET",
      "url": "https://api.example.com/weather",
      "parameters": {
        "city": {
          "type": "string",
          "description": "城市名",
          "required": true
        }
      }
    }
  ]
}
```

HTTP Action 工具名需为 1-64 位的字母、数字、下划线或短横线。`GET` 请求会把参数放入 query string，其他方法会把参数作为 JSON body 发送。URL 支持 `{param}` 路径占位，例如 `https://api.example.com/weather/{city}`。

## Trace 调用链

每次用户发送消息会创建一条 `trace_runs` 记录，执行过程中的节点写入 `trace_spans`：

- `setup`：Skill/MCP 工具发现结果。
- `llm`：每轮模型输入、输出、状态和耗时。
- `tool`：Skill、SkillFile 或 MCP 工具的参数、结果、错误和耗时。

Trace 状态包括 `running`、`success`、`error`、`cancelled` 和 `timeout`。Trace 数据按登录
用户隔离；仅新产生的对话会被记录，历史对话不会自动补录。数据库表会在后端启动时自动创建。

## 本地 Python Runtime

聊天 Agent 和工作流 Agent 会按运行上下文获得一个结构化工具：

- `ExecutePython`：执行 LLM 生成的 Python 代码。

聊天页可上传 CSV、Excel、Word、PDF、JSON、Markdown 和文本文件。模型仅能看到逻辑 `file_id`，脚本通过下列变量访问输入和输出：

```python
from pathlib import Path

input_path = Path(next(iter(INPUT_FILES.values())))
output_path = Path(OUTPUT_DIR) / "summary.json"
output_path.write_text('{"ok": true}', encoding="utf-8")
result = {"message": "处理完成"}
```

Runtime 使用“每用户一个容器”的模型；`workspace_id` 只区分同一用户容器内的目录。
Runtime 与进程插件复用这个容器，默认允许网络、非 root、只读根文件系统，并限制为 1 CPU、512MB 内存、128 个进程，
单次执行最多 30 秒。空闲 30 分钟停止，7 天未使用删除容器但保留用户目录。
生产环境应把 Sandbox Service 放到独立 Linux 节点，并安装 gVisor 后设置
`SANDBOX_CONTAINER_RUNTIME=runsc`。
同一用户的 Runtime、依赖安装和插件调用串行执行，共享 `/workspaces`；插件的版本依赖
目录相互独立，同用户代码之间不提供文件或凭据隔离。旧容器在下一次空闲执行时按新版
配置重建，已有挂载文件保留。每个 Docker 节点运行一个 Sandbox Manager。

Runtime Worker 的调用链：

```text
Agent / LangGraph
    ↓ ExecutePython
FastAPI：校验代码、文件权限并创建 queued 记录
    ↓ RPUSH
Redis：runtime:execution:queue
    ↓ BLPOP
runtime_worker：领取任务并更新为 running
    ↓
Sandbox Service：按 user_id 获取或创建唯一容器
    ↓
用户容器：在 /workspaces/{workspace_id} 中运行 child_runner.py
    ↓
MySQL：保存状态、日志和 Artifact
    ↓ Redis 结果通道
FastAPI：取得结果并作为 ToolMessage 返回给 LLM
```

当前 API、Worker 和 Sandbox Service 使用共享 `RUNTIME_DATA_DIR`。生产环境拆分节点时，
应使用受控共享卷，或将输入文件和 Artifact 改为 MinIO、S3、OSS 等对象存储。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 无 | LLM API Key（必填） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 基础地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名称 |
| `JWT_SECRET` | `agent-platform-secret-2026` | JWT 密钥 |
| `EXTERNAL_API_CHAT_RATE_LIMIT` | `60` | 单个 API Key 每分钟允许的外部聊天请求数 |
| `API_KEY_AUTH_RATE_LIMIT_PER_IP` | `120` | 单个来源 IP 每 5 分钟允许的 API Key 认证次数 |
| `API_KEY_MANAGEMENT_RATE_LIMIT` | `5` | 单个用户每分钟允许的密钥生成或吊销次数 |
| `SERVER_PORT` | `20000` | 后端端口 |
| `DB_HOST` | `127.0.0.1` | MySQL 主机 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户名 |
| `DB_PASSWORD` | `123456` | MySQL 密码 |
| `DB_NAME` | `agent_platform_langchain` | MySQL 数据库名 |
| `REDIS_HOST` | `127.0.0.1` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_DB` | `0` | Redis 数据库编号 |
| `REDIS_PASSWORD` | 无 | Redis 密码 |
| `WORKFLOW_EVENT_STREAM_TTL_SECONDS` | `86400` | 工作流事件 Stream 保留时间（秒） |
| `WORKFLOW_EVENT_STREAM_MAXLEN` | `20000` | 每个工作流事件 Stream 的近似最大长度 |
| `PYTHON_RUNTIME_ENABLED` | `true` | 是否向 Agent 注册本地 Python Runtime 工具 |
| `PYTHON_RUNTIME_TIMEOUT_SECONDS` | `30` | 默认执行超时秒数 |
| `PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS` | `30` | Agent 可请求的最大超时秒数 |
| `PYTHON_RUNTIME_MEMORY_MB` | `512` | 兼容配置；实际容器限制由 Sandbox Service 设置 |
| `PYTHON_RUNTIME_MAX_UPLOAD_MB` | `20` | 单个上传文件大小限制 |
| `PYTHON_RUNTIME_MAX_OUTPUT_MB` | `20` | 单次执行产出文件总大小限制 |
| `RUNTIME_WORKER_QUEUE_NAME` | `runtime:execution:queue` | Runtime Worker 使用的 Redis 任务队列名称 |
| `SANDBOX_SERVICE_URL` | `http://127.0.0.1:20002` | 独立 Sandbox Service 地址 |
| `SANDBOX_SERVICE_TOKEN` | `change-me-in-production` | API/Worker 与 Sandbox Service 的内部认证密钥 |
| `SANDBOX_CONTAINER_RUNTIME` | 空 | 生产 Linux 上可设置为 `runsc` 启用 gVisor |
| `SANDBOX_HOST_DATA_ROOT` | 自动识别 | 远程 Docker daemon 可见的 Runtime 数据根目录 |
| `SANDBOX_NETWORK_ENABLED` | `true` | Sandbox Manager 的用户容器网络开关；本次 Compose 固定开启 |
| `RUNTIME_WORKER_QUEUE_WAIT_SECONDS` | `30` | API 允许任务排队等待 Worker 的最长时间 |
| `RUNTIME_WORKER_RESULT_TTL_SECONDS` | `3600` | Worker 执行结果在 Redis 中的保留秒数 |

## License

Private
