# Agent Platform

一个完整的 AI Agent 管理平台，支持：
- 🔐 **用户登录/注册** - JWT 认证
- 🤖 **Agent 管理** - 创建、编辑、删除 Agent，配置系统提示词、模型、温度
- 📝 **Skill 管理** - 上传 SKILL.md 文件，手动创建 Skill
- 🔌 **MCP 配置** - 配置多个 MCP Server 连接，动态发现和调用工具
- 💬 **流式对话** - SSE 流式响应，多轮 Tool Call 自动循环
- 📱 **Web UI** - Vue 3 + Element Plus 前端

## 目录结构

```
agent_platform/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置（端口、密钥、MySQL 连接）
│   ├── database.py          # MySQL 数据库层（aiomysql）
│   ├── auth.py              # JWT 认证
│   ├── agents.py            # Agent CRUD
│   ├── skills.py            # Skill 管理
│   ├── mcp_configs.py       # MCP 配置管理
│   ├── mcp_client.py        # MCP 客户端（Streamable HTTP）
│   ├── chat_engine.py       # 流式对话核心（多轮 Tool Call）
│   ├── requirements.txt     # Python 依赖
│   ├── sql/init.sql         # MySQL 初始化脚本
│   └── data/                # 上传的 Skill 文件
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

## 快速开始

### 1. MySQL 初始化

```bash
# 创建数据库和表结构
mysql -u root -p < backend/sql/init.sql
```

### 2. 后端启动

```bash
cd agent_platform/backend
pip install -r requirements.txt

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
python main.py
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
cd ../backend
python main.py
```

访问 `http://127.0.0.1:20000` 即可使用完整系统。

## API 接口

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/register` | 注册 |
| GET | `/api/auth/me` | 当前用户信息 |
| POST | `/api/auth/logout` | 登出 |

### Agent
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/agentsList` | Agent 列表 |
| GET | `/api/agents/{id}` | Agent 详情 |
| POST | `/api/agents` | 创建 Agent |
| PUT | `/api/agents/{id}` | 更新 Agent |
| DELETE | `/api/agents/{id}` | 删除 Agent |

### Skill
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/skills` | Skill 列表 |
| POST | `/api/skills/upload` | 上传 SKILL.md |
| POST | `/api/skills` | 手动创建 Skill |
| DELETE | `/api/skills/{id}` | 删除 Skill |

### MCP 配置
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/mcp-configs` | MCP 配置列表 |
| POST | `/api/mcp-configs` | 创建 MCP 配置 |
| PUT | `/api/mcp-configs/{id}` | 更新 MCP 配置 |
| DELETE | `/api/mcp-configs/{id}` | 删除 MCP 配置 |

### 会话 & 对话
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/sessions` | 会话列表 |
| POST | `/api/sessions` | 创建会话 |
| PUT | `/api/sessions/{id}` | 重命名会话 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/sessions/{id}/messages` | 历史消息 |
| GET | `/api/chat/stream` | SSE 流式对话 |

## 使用流程

1. **注册/登录** → 进入仪表盘
2. **创建 Skill** → 上传 SKILL.md 或手动输入内容
3. **配置 MCP** → 添加 MCP Server 连接信息
4. **创建 Agent** → 设置名称、系统提示词、最大迭代次数，并关联 Skill 和 MCP
5. **开始对话** → 选择 Agent 创建会话，开始流式对话

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
```

`agents.iteration_count` 表示单次对话允许的最大工具调用迭代次数，取值范围为 `1–100`，默认值为 `6`。已有数据库会在后端启动时自动补充该字段。

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
