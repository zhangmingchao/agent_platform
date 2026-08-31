# Agent Runtime 实现文档

## 1. 文档目标

本文描述 Agent Platform 当前代码中的 Agent Runtime 与 Python Tool Runtime 实现，包括：

- Agent 如何发现并调用代码执行 Tool。
- Runtime Worker、Sandbox Service 和用户沙箱容器之间的职责边界。
- Redis、MySQL、文件系统和 Docker 分别保存什么数据。
- 每个核心类、数据模型和函数的作用。
- 单 Worker、多 Worker、用户容器和 workspace 之间的数量关系。
- 运行、排障、安全限制和后续扩展方式。

本文以当前代码为准，不把尚未实现的设计描述成现有能力。

---

## 2. 术语定义

### 2.1 Agent Runtime

Agent Runtime 是负责大模型推理、Tool Calling 和执行编排的部分，包括：

- 创建 LangGraph Agent。
- 调用 LLM。
- 注册 Skill、MCP 和 Python Runtime Tool。
- 处理多轮 Tool Calling。
- 管理聊天上下文和工作流上下文。
- 输出 SSE 事件。
- 记录 Trace。

### 2.2 Tool Runtime

Tool Runtime 是 Agent 调用具体工具时的执行环境。本文重点描述 Python Tool Runtime：

- 接收模型生成的 Python 代码。
- 校验代码和输入文件。
- 将任务写入 Redis。
- 由独立 Worker 消费任务。
- 在用户私有 Docker 容器中执行代码。
- 返回日志、结果和 Artifact。

### 2.3 Sandbox Service

Sandbox Service 是唯一允许访问 Docker Engine 的组件，负责用户容器的创建、复用、启动、执行、停止和删除。

### 2.4 Workspace

`workspace_id` 是同一用户容器中的目录隔离标识，不会创建新的 Docker 容器。

例如：

```text
用户 1 的容器
└── /workspaces
    ├── session-20
    ├── session-21
    └── workflow-7
```

---

## 3. 总体架构

```text
┌────────────────────────────────────────────────────────────────────┐
│                             前端                                   │
│                    Chat / Workflow / 文件上传                      │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ HTTP + SSE
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        FastAPI 后端                                │
│                                                                    │
│  LangGraph Agent Runtime                                           │
│  ├── LLM                                                           │
│  ├── Skill Tool                                                    │
│  ├── MCP Tool                                                      │
│  ├── HTTP Action                                                   │
│  └── ExecutePython / RunSkillScript                                │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ 创建执行记录、准备目录、任务入队
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                            Redis                                   │
│  runtime:execution:queue                                           │
│  runtime:execution:{execution_id}:result                           │
│  runtime:execution:{execution_id}:cancelled                        │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ BLPOP
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Runtime Worker                                │
│  ├── 领取任务                                                      │
│  ├── 检查取消标记                                                  │
│  ├── 二次校验工作目录和代码                                        │
│  ├── 调用 Sandbox Service                                         │
│  ├── 登记结果与 Artifact                                           │
│  └── 发布 Redis 结果                                               │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ 内部 HTTP + Bearer Token
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Sandbox Service                               │
│  ├── Docker 容器生命周期                                          │
│  ├── 每用户执行锁                                                  │
│  ├── 用户容器创建与复用                                            │
│  ├── docker exec                                                   │
│  └── 空闲容器清理                                                  │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ Docker API
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       用户 1 容器       用户 2 容器       用户 N 容器
       /workspaces       /workspaces       /workspaces
```

---

## 4. 组件数量和关系

| 组件 | 当前数量 | 是否可扩展 | 说明 |
|---|---:|---:|---|
| FastAPI 后端 | 通常 1 个 | 可以 | 提供 Agent、API 和 SSE |
| Redis | 1 个 | 可以部署高可用 | 保存 Runtime 队列、结果和取消标记 |
| Runtime Worker | 当前手工启动 1 个 | 可以多个 | 每个 Worker 同一时间处理一个任务 |
| Sandbox Service | 当前 1 个 | 后续可多个节点 | 唯一直接访问 Docker Engine 的服务 |
| 用户沙箱容器 | 每个活跃用户最多 1 个 | 按用户增长 | 容器停止或删除后按需重建 |
| Workspace | 每个会话、工作流或业务空间一个 | 按目录增长 | 位于用户容器内部，不是独立容器 |

准确关系是：

```text
Runtime Worker 不是一个用户对应一个 Worker。
Runtime Worker 也不是直接管理 Docker。

Worker 消费任意用户任务
       ↓
Sandbox Service 根据 user_id 找到用户容器
       ↓
根据 workspace_id 找到容器内工作目录
```

### 4.1 一个 Worker 的行为

当前 `run_runtime_worker()` 是单循环执行：

```text
领取任务 A → 等待 A 完成 → 领取任务 B → 等待 B 完成
```

因此一个 Worker 同时只执行一个任务。

### 4.2 多个 Worker 的行为

可以启动多个 Worker 竞争 Redis List：

```text
Redis Queue
├── Worker 1 → 用户 1
├── Worker 2 → 用户 2
└── Worker 3 → 用户 3
```

Redis `BLPOP` 可以保证一条队列消息只被一个 Worker 领取。

### 4.3 同一用户的并发限制

Sandbox Service 使用 `_user_locks[user_id]`：

```text
用户 1 的任务 A → 执行中
用户 1 的任务 B → 等待用户锁
用户 2 的任务 A → 可以并行执行
```

当前锁是 Sandbox Service 单进程内的 `asyncio.Lock`。如果未来部署多个 Sandbox Service 实例，需要改成 Redis 分布式锁或数据库 Lease。

---

## 5. 完整调用流程

### 5.1 Agent 注册 Runtime Tool

Agent 创建时，`create_agent_instance()` 调用 `build_all_tools()`：

```text
create_agent_instance
  └── build_all_tools
      ├── build_skill_tools
      ├── build_runtime_tools
      └── build_mcp_langchain_tools
```

`build_runtime_tools()` 根据 `RuntimeContext` 创建：

- `ExecutePython`
- `RunSkillScript`

### 5.2 LLM 决定调用 Tool

LLM 收到工具名称、描述和参数 Schema 后，可以产生：

```json
{
  "name": "ExecutePython",
  "args": {
    "code": "result = {'total': 100}",
    "input_file_ids": [],
    "timeout_seconds": 30
  }
}
```

LangGraph 调用 `execute_python()`，再进入 `execute_python_code()`。

### 5.3 API 侧准备执行任务

`prepare_runtime_execution()` 执行：

1. 使用 AST 静态策略校验代码。
2. 限制执行超时。
3. 验证输入文件都属于当前用户。
4. 生成 `execution_id`。
5. 生成用户、workspace 和 execution 目录。
6. 复制输入文件。
7. 写入 `main.py` 和 `runtime.json`。
8. 在 MySQL 创建 `queued` 状态记录。
9. 返回不包含完整代码的队列任务。

任务结构：

```json
{
  "executionId": "uuid",
  "userId": 1,
  "workspaceId": "session-20",
  "timeoutSeconds": 30,
  "context": {
    "user_id": 1,
    "workspace_id": "session-20",
    "session_id": 20,
    "workflow_run_id": null,
    "workflow_step_id": null,
    "node_id": null
  }
}
```

完整代码不写入 Redis，而是保存在受控 execution 目录中。

### 5.4 Redis 入队和等待

`execute_python_code()` 调用：

```text
enqueue_runtime_task(task)
       ↓
Redis RPUSH runtime:execution:queue
       ↓
wait_runtime_result(execution_id)
       ↓
BLPOP runtime:execution:{execution_id}:result
```

API 等待时间为：

```text
最大排队时间 + 代码执行超时 + 10 秒收尾缓冲
```

如果超时未得到结果：

- 写入 Redis 取消标记。
- 将仍处于 `queued` 的数据库记录改成 `failed`。
- 返回“Worker 未启动、繁忙或失联”。

### 5.5 Worker 领取任务

`run_runtime_worker()` 持续调用 `claim_runtime_task()`：

```text
BLPOP runtime:execution:queue
       ↓
process_runtime_task(task)
```

Worker 首先检查取消标记。排队期间已取消的任务不会进入沙箱。

### 5.6 Worker 调用 Sandbox Service

`execute_runtime_task()` 二次检查：

- `userId` 与 `RuntimeContext.user_id` 是否一致。
- `workspaceId` 与上下文计算结果是否一致。
- execution 目录是否位于用户目录内。
- `main.py`、`runtime.json` 和输出目录是否存在。
- 落盘后的代码是否仍通过安全策略。

之后通过 `execute_in_sandbox()` 调用：

```text
POST {SANDBOX_SERVICE_URL}/v1/executions
Authorization: Bearer {SANDBOX_SERVICE_TOKEN}
```

### 5.7 Sandbox Service 调度用户容器

Sandbox Service 根据 `userId` 查找带有以下 Label 的容器：

```text
agent.platform.sandbox=true
agent.platform.user_id={user_id}
```

容器不存在时创建；存在但已停止时启动；正在运行时直接复用。

容器名称：

```text
agent-sandbox-user-{user_id}
```

### 5.8 容器执行代码

Sandbox Service 使用 `docker exec`：

```text
timeout --signal=KILL 30s
python -I /opt/sandbox/child_runner.py runtime.json
```

`child_runner.py` 为用户代码提供：

- `INPUT_DIR`
- `OUTPUT_DIR`
- `INPUT_FILES`
- `RUNTIME_ARGS`

用户代码可以将最终结构化数据赋值给 `result`，由 child runner 写入：

```text
output/result.json
```

其他写入 `OUTPUT_DIR` 的文件会作为 Artifact 登记。

### 5.9 结果返回 Agent

```text
用户容器
  ↓ stdout / stderr / result / files
Sandbox Service
  ↓ JSON
Runtime Worker
  ↓ MySQL 状态 + Redis result
FastAPI Runtime Tool
  ↓ ToolMessage
LangGraph Agent
  ↓ 最终自然语言回答
前端 SSE
```

标准结果：

```json
{
  "executionId": "uuid",
  "status": "completed",
  "exitCode": 0,
  "stdout": "",
  "stderr": "",
  "error": "",
  "result": {},
  "artifacts": []
}
```

---

## 6. 核心类和数据模型

### 6.1 Agent 层

| 类/函数 | 文件 | 作用 |
|---|---|---|
| `create_agent_instance()` | `backend/core/agent_factory.py` | 创建 LangGraph ReAct Agent，装配 LLM、Skill、MCP 和 Runtime Tool |
| `build_all_tools()` | `backend/core/agent_factory.py` | 汇总所有可供 Agent 调用的工具 |
| `build_runtime_tools()` | `backend/runtime/tools.py` | 根据 RuntimeContext 创建 Python Runtime 工具 |
| `ExecutePythonInput` | `backend/runtime/tools.py` | 定义 ExecutePython 对 LLM 暴露的参数 Schema |
| `RunSkillScriptInput` | `backend/runtime/tools.py` | 定义 Skill 脚本工具的参数 Schema |
| `StructuredTool` | LangChain | 将异步 Python 函数包装成 LLM 可调用 Tool |

### 6.2 Runtime 上下文

#### `RuntimeContext`

文件：`backend/runtime/models.py`

不可变数据类，用于绑定一次执行所属的业务上下文：

| 字段 | 作用 |
|---|---|
| `user_id` | 用户隔离主键，同时决定使用哪个用户容器 |
| `workspace_id` | 用户容器内的工作目录标识 |
| `session_id` | 单 Agent 会话关联 |
| `workflow_run_id` | 工作流运行关联 |
| `workflow_step_id` | 工作流步骤关联 |
| `node_id` | 工作流画布节点关联 |

### 6.3 Runtime 服务层

| 函数 | 文件 | 作用 |
|---|---|---|
| `execute_python_code()` | `backend/services/runtime_service.py` | Tool 调用总入口：准备、入队、等待结果 |
| `prepare_runtime_execution()` | 同上 | 校验代码和文件，创建 execution 工作目录和数据库记录 |
| `execute_runtime_task()` | 同上 | Worker 侧执行逻辑：二次校验、调用沙箱、解析结果和 Artifact |
| `save_runtime_file()` | 同上 | 保存用户上传的 Runtime 输入文件 |
| `get_runtime_file()` | 同上 | 按用户查询单个 Runtime 文件 |
| `get_runtime_files()` | 同上 | 批量验证文件归属并保持输入顺序 |
| `resolve_skill_script()` | 同上 | 校验 Skill 脚本路径，防止目录穿越 |
| `_workspace_id()` | 同上 | 将上下文转换成安全 workspace 标识 |
| `_register_artifacts()` | 同上 | 登记沙箱生成文件并返回下载信息 |
| `_rewrite_virtual_input_paths()` | 同上 | 兼容模型生成的 `/mnt/data/文件名` 路径 |

### 6.4 Redis 队列层

| 函数 | 文件 | 作用 |
|---|---|---|
| `enqueue_runtime_task()` | `backend/runtime/queue.py` | 使用 RPUSH 将任务放入队列 |
| `claim_runtime_task()` | 同上 | 使用 BLPOP 阻塞领取任务 |
| `publish_runtime_result()` | 同上 | 将最终结果写入 execution 专属结果 List，并设置 TTL |
| `wait_runtime_result()` | 同上 | API 侧通过短周期 BLPOP 等待结果 |
| `cancel_runtime_task()` | 同上 | 设置排队任务取消标记 |
| `is_runtime_task_cancelled()` | 同上 | Worker 执行前检查取消标记 |
| `runtime_result_key()` | 同上 | 生成 execution 结果 Key |
| `runtime_cancel_key()` | 同上 | 生成 execution 取消 Key |

### 6.5 Runtime Worker

| 函数 | 文件 | 作用 |
|---|---|---|
| `run_runtime_worker()` | `backend/runtime_worker.py` | 初始化数据库和 Redis，持续消费队列 |
| `process_runtime_task()` | 同上 | 处理单个任务、取消检查、异常兜底和结果发布 |
| `_failed_result()` | 同上 | 生成统一失败结果结构 |
| `main()` | 同上 | 启动 Worker asyncio 事件循环 |

### 6.6 Sandbox 客户端

| 类/函数 | 文件 | 作用 |
|---|---|---|
| `SandboxServiceError` | `backend/runtime/sandbox_client.py` | 表示沙箱不可用、拒绝执行或返回无效数据 |
| `execute_in_sandbox()` | 同上 | 使用内部 Token 调用 Sandbox Service |

### 6.7 Sandbox Service

| 类/函数 | 文件 | 作用 |
|---|---|---|
| `ExecutionRequest` | `sandbox_service/app.py` | 沙箱执行 HTTP 请求模型 |
| `require_internal_token()` | 同上 | 校验 Sandbox Service 内部 Bearer Token |
| `_container_name()` | 同上 | 生成用户容器名称 |
| `_find_user_container()` | 同上 | 根据 Docker Label 查找用户容器 |
| `_ensure_user_container()` | 同上 | 创建、启动或复用用户容器 |
| `_validate_request_paths()` | 同上 | 校验 execution、workspace 和配置文件路径 |
| `_prepare_permissions()` | 同上 | 为宿主后端和容器用户准备目录权限 |
| `_execute_sync()` | 同上 | 在用户容器内执行 child runner 并收集输出 |
| `execute_code()` | 同上 | `/v1/executions` HTTP 接口，并使用用户锁串行化执行 |
| `_cleanup_sync()` | 同上 | 停止空闲容器、删除长期未使用容器 |
| `_cleanup_loop()` | 同上 | 周期性执行容器清理 |
| `health()` | 同上 | 验证 Docker Engine 并返回沙箱镜像信息 |

### 6.8 静态安全策略

| 类/函数 | 文件 | 作用 |
|---|---|---|
| `RuntimePolicyError` | `backend/runtime/policy.py` | 代码不符合安全策略时抛出的异常 |
| `validate_python_code()` | 同上 | AST 解析并检查导入、函数调用和危险属性 |
| `ALLOWED_IMPORT_ROOTS` | 同上 | Python 允许导入的顶级模块集合 |
| `DENIED_CALL_NAMES` | 同上 | 禁止调用的危险内置函数 |
| `DENIED_ATTRIBUTE_NAMES` | 同上 | 禁止访问的反射和逃逸相关属性 |

### 6.9 容器内 Child Runner

| 函数 | 文件 | 作用 |
|---|---|---|
| `main()` | `backend/runtime/child_runner.py` | 读取 runtime.json，安装审计钩子，构建运行变量并执行用户代码 |
| `_install_audit_hook()` | 同上 | 使用 Python Audit Hook 限制文件、网络、子进程和动态库操作 |
| `_is_relative_to()` | 同上 | 校验文件路径是否位于允许的目录边界内 |

Child Runner 运行在用户沙箱容器中，不运行在 FastAPI 或 Runtime Worker 进程中。

### 6.10 Runtime HTTP API

| 接口/函数 | 文件 | 作用 |
|---|---|---|
| `POST /api/runtime/files` | `backend/routers/runtime.py` | 上传 Runtime 输入文件 |
| `GET /api/runtime/files/{file_id}` | 同上 | 下载输入文件或 Artifact |
| `_validate_session()` | 同上 | 防止将文件绑定到其他用户会话 |

---

## 7. Redis 数据结构

### 7.1 任务队列

```text
Key: runtime:execution:queue
Type: List
写入: RPUSH
消费: BLPOP
```

### 7.2 执行结果

```text
Key: runtime:execution:{execution_id}:result
Type: List
写入: Worker RPUSH
消费: API BLPOP
TTL: RUNTIME_WORKER_RESULT_TTL_SECONDS，默认 3600 秒
```

### 7.3 取消标记

```text
Key: runtime:execution:{execution_id}:cancelled
Type: String
Value: 1
TTL: 根据任务最大超时设置
```

当前取消标记只能阻止还在排队、尚未被 Worker 执行的任务。正在容器中运行的任务主要依靠 `timeout` 强制终止。

---

## 8. 文件系统结构

```text
backend/data/runtime/
├── files/
│   └── {user_id}/
│       └── {file_id}/
│           └── uploaded-file.xlsx
└── users/
    └── {user_id}/
        ├── .sandbox-last-active
        └── workspaces/
            └── {workspace_id}/
                └── executions/
                    └── {execution_id}/
                        ├── source/main.py
                        ├── input/
                        ├── output/
                        │   ├── result.json
                        │   └── artifact.xlsx
                        ├── runtime.json
                        ├── stdout.log
                        └── stderr.log
```

容器中统一挂载为：

```text
/workspaces/{workspace_id}/executions/{execution_id}/
```

---

## 9. MySQL 数据职责

### 9.1 `code_executions`

保存：

- execution ID
- user/workspace/session/workflow/node 关联
- 代码 SHA-256，不保存完整源码
- 状态：`queued/running/completed/failed/timed_out`
- 超时、退出码
- stdout/stderr
- result JSON
- Sandbox 容器 ID
- 开始和结束时间

### 9.2 `runtime_files`

保存：

- 文件逻辑 ID
- 所属用户和会话
- 所属 execution
- 文件名、存储路径、MIME、大小、SHA-256
- 文件类型：`input/artifact`

---

## 10. 用户容器安全限制

当前用户容器配置：

| 限制 | 当前设置 |
|---|---|
| 用户 | 非 root，默认 `10001:10001` |
| 网络 | `network_disabled=true` |
| 根文件系统 | 只读 |
| CPU | 默认 1 CPU |
| 内存 | 默认 512 MB |
| Swap | 与内存相同，避免额外 Swap |
| PID | 默认最多 128 |
| Linux Capability | `cap_drop=ALL` |
| 提权 | `no-new-privileges` |
| `/tmp` | 128 MB tmpfs，`noexec,nosuid,nodev` |
| 工作目录 | 只挂载当前用户的 `/workspaces` |
| 执行超时 | 最大 30 秒，超时发送 KILL |
| Python | 使用 `python -I` 隔离模式 |
| stdout/stderr | 各最多捕获 1 MB |

AST 静态策略只是第一层防误用，Docker 隔离才是主要安全边界。生产环境仍建议使用独立 Linux 沙箱节点和 gVisor。

---

## 11. 容器生命周期

```text
第一次执行
  ↓
创建用户容器
  ↓
后续执行复用容器
  ↓
空闲 30 分钟
  ↓
停止容器
  ↓
再次执行时自动启动
  ↓
7 天未使用
  ↓
删除容器
```

Workspace 文件是否保留与容器生命周期分离。容器删除后，宿主机 Runtime Volume 中的 workspace 仍可按产品数据策略保留或清理。

---

## 12. 启动方式

### 12.1 启动 Redis、MySQL 和 FastAPI

按项目现有方式启动基础服务和后端。

### 12.2 启动 Sandbox Service

```bash
docker compose -f docker-compose.sandbox.yml up -d --build
```

健康检查：

```bash
curl -H "Authorization: Bearer ${SANDBOX_SERVICE_TOKEN}" \
  http://127.0.0.1:20002/health
```

### 12.3 启动 Runtime Worker

```bash
backend/.venv-langchan/bin/python -m backend.runtime_worker
```

Runtime Worker 当前未加入 Docker Compose，需要单独保持运行。

---

## 13. 当前故障表现和排查

### 13.1 Worker 未启动

表现：

- FastAPI 正常。
- Sandbox Service 正常。
- 任务不断进入 `runtime:execution:queue`。
- Agent 最终提示等待 Worker 超时。

检查：

```bash
ps aux | grep runtime_worker
redis-cli LLEN runtime:execution:queue
```

### 13.2 Sandbox Service 未启动

表现：Worker 能领取任务，但执行结果为 Sandbox Service 无法连接。

检查：

```bash
docker compose -f docker-compose.sandbox.yml ps
docker compose -f docker-compose.sandbox.yml logs sandbox-service
```

### 13.3 Token 不一致

表现：Sandbox Service 返回 401：

```text
Sandbox Service 认证失败
```

需要保证后端和 Sandbox Service 使用相同的 `SANDBOX_SERVICE_TOKEN`。

### 13.4 Redis 不可用

表现：API 无法入队，Worker 无法领取任务，结果通道不可用。

检查：

```bash
redis-cli ping
```

### 13.5 队列积压

检查：

```bash
redis-cli LLEN runtime:execution:queue
```

一个 Worker 串行处理任务；任务量增加后应增加 Worker 数量并完善任务 Lease。

---

## 14. 当前架构边界

当前已实现：

- FastAPI 与代码执行进程分离。
- Redis 异步任务队列和结果通道。
- Worker 与 Docker API 解耦。
- 每用户一个私有 Docker 容器。
- workspace 目录隔离。
- 非 root、无网络、只读根文件系统和资源限制。
- 代码 AST 校验、执行超时和 Artifact 管理。
- 排队任务取消标记。

当前尚未完整实现：

- Runtime Worker 自动部署和健康检查。
- Redis Pending/Ack、任务 Lease 和 Worker 崩溃恢复。
- 正在执行任务的主动取消。
- 多 Sandbox Service 下的分布式用户锁。
- 用户磁盘配额和 workspace 自动清理。
- 镜像漏洞扫描与镜像版本发布策略。
- gVisor 生产隔离。
- Runtime Worker 和 Sandbox 的完整监控告警。

---

## 15. 推荐的下一步升级

### P0

1. 将 Runtime Worker 加入 Docker Compose，配置自动重启和健康检查。
2. 将 Redis List 改为具备 Ack/Lease 的可靠队列，避免 Worker 领取任务后崩溃导致任务丢失。
3. 增加执行中取消能力。

### P1

1. 使用 Redis 分布式用户锁支持多个 Sandbox Service。
2. 增加用户并发、CPU 时间和每日执行次数配额。
3. 增加 workspace 磁盘配额和清理任务。
4. 增加队列深度、执行耗时、失败率和容器数量监控。

### P2

1. 生产环境迁移至独立 Linux Sandbox 节点。
2. 使用 gVisor `runsc`。
3. 增加沙箱镜像签名、SBOM 和漏洞扫描。
4. 根据业务规模演进为多节点 Runtime Scheduler。

---

## 16. 总结

当前 Agent Runtime 的准确描述是：

> LangGraph Agent 根据用户任务调用 Python Runtime Tool；FastAPI 负责校验、准备工作目录并将任务写入 Redis；一个或多个 Runtime Worker 消费所有用户任务并调用 Sandbox Service；Sandbox Service 根据 `user_id` 创建或复用每用户一个的私有 Docker 容器，根据 `workspace_id` 隔离容器内目录，并在受限环境中执行代码。

核心数量关系：

```text
Worker：当前 1 个，可以扩容多个
Sandbox Service：当前 1 个
用户容器：每个活跃用户最多 1 个
Workspace：同一用户可以有多个
Execution：每次 Tool 调用生成一个
```
