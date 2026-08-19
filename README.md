# Agent Platform

一个完整的 AI Agent 管理平台，支持：
- 🔐 **用户登录/注册** - JWT 认证
- 🤖 **Agent 管理** - 创建、编辑、删除 Agent，配置系统提示词、模型、温度和工具迭代次数
- 📝 **Skill 管理** - 上传 ZIP 技能包（`SKILL.md` + `references/`），在线编辑与 Markdown 预览
- 🔌 **MCP 配置** - 配置多个 MCP Server，动态发现、查看和调试工具
- 💬 **流式对话** - SSE 流式响应，多轮 Tool Call 自动循环
- 🔎 **Trace 调用链** - 记录每次对话的 LLM 轮次、工具调用、输入输出、错误与耗时
- 📱 **Web UI** - Vue 3 + Element Plus 前端

## 目录结构

```
agent_platform/
├── backend/
│   ├── main.py              # FastAPI 入口
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
│   ├── sql/init.sql         # MySQL 初始化脚本
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
| PyJWT | JWT 认证 |
| OpenAI SDK | LLM 调用 |
| Requests | MCP 通信 |

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

### 1. MySQL 初始化

```bash
# 创建数据库和表结构
mysql -u root -p < backend/sql/init.sql
```

### 2. 后端启动

```bash
cd agent_platform
pip install -r backend/requirements.txt

# 配置环境变量（可选）
export DEEPSEEK_API_KEY="your-api-key"
export DEEPSEEK_MODEL="deepseek-chat"
export JWT_SECRET="your-secret"
export SERVER_PORT="20000"

# 配置 MySQL 连接（可选，默认值如下）
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD="123456"
export DB_NAME="agent_platform"

# 启动服务
python -m backend.main
```

后端启动后：
- API 地址: `http://127.0.0.1:20000`
- 默认账号: `admin / 123456`
- 数据库: MySQL（使用 `agent_platform` 数据库）

### 3. 前端开发

```bash
cd agent_platform/frontend
npm install
npm run dev
```

前端开发服务器: `http://127.0.0.1:20001`（自动代理 `/api` 到后端 20000 端口）

### 4. 生产部署

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

### 会话 & 对话
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/sessions?agent_id={id}` | 按当前用户与 Agent 查询会话 |
| POST | `/api/sessions` | 创建会话 |
| PUT | `/api/sessions/{id}` | 重命名会话 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/sessions/{id}/messages` | 历史消息 |
| POST | `/api/chat/stream` | SSE 流式对话（JSON 请求体） |

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

### Trace 调用链
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/traces` | 当前用户的 Trace 列表 |
| GET | `/api/traces/{id}` | Trace 详情与 Span 调用链 |

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
agents         Agent 表（id, user_id, name, description, system_prompt, model, temperature, iteration_count）
skills         Skill 表（id, user_id, name, description, content）
mcp_configs    MCP 配置表（id, user_id, name, base_url, endpoint, description）
agent_skills   Agent-Skill 关联表（agent_id, skill_id）
agent_mcps     Agent-MCP 关联表（agent_id, mcp_id）
chat_sessions  会话表（id, user_id, agent_id, title）
chat_messages  消息表（id, session_id, role, content）
trace_runs     对话 Trace（user_id, agent_id, session_id, status, input/output, duration）
trace_spans    Trace 节点（trace_id, span_type, round_no, input/output, error, duration）
multi_agent_workflows  多 Agent 工作流配置
multi_agent_runs       多 Agent 工作流运行记录
multi_agent_run_steps  多 Agent 工作流步骤记录
```

`agents.iteration_count` 表示单次对话允许的最大工具调用迭代次数，取值范围为 `1–100`，默认值为 `6`。已有数据库会在后端启动时自动补充该字段。

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

Trace 状态包括 `running`、`success`、`error` 和 `cancelled`。Trace 数据按登录用户隔离；仅新产生的对话会被记录，历史对话不会自动补录。数据库表会在后端启动时自动创建。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 无 | LLM API Key（必填） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 基础地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 模型名称 |
| `JWT_SECRET` | `agent-platform-secret-2026` | JWT 密钥 |
| `SERVER_PORT` | `20000` | 后端端口 |
| `DB_HOST` | `127.0.0.1` | MySQL 主机 |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | MySQL 用户名 |
| `DB_PASSWORD` | `123456` | MySQL 密码 |
| `DB_NAME` | `agent_platform` | MySQL 数据库名 |

## License

Private
