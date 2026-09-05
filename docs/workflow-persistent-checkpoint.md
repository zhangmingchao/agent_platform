# 工作流持久化 Checkpoint 与人工审批恢复

## 目标

工作流运行使用稳定的 LangGraph `thread_id`，将运行级 State 和人工审批暂停点保存到
Redis Checkpointer。服务实例变化后，只要 Redis 中的 Checkpoint 仍然存在，就可以通过
同一个 `run_id` 恢复执行。

## 状态分层

```text
WorkflowRuntimeState（整个工作流）
    ├── AgentPlatformState（Agent 节点 1 内部）
    ├── AgentPlatformState（Agent 节点 2 内部）
    └── AgentPlatformState（Agent 节点 3 内部）
```

- 工作流级 `thread_id`：`workflow_run_{run_id}`，从开始到结束保持不变。
- Agent 节点级 `thread_id`：继续按运行和步骤隔离，防止不同 Agent 的消息及工具结果互相污染。
- `WorkflowRuntimeState`：保存工作流配置快照、当前输入、节点游标、审批状态和最终输出。
- `AgentPlatformState`：保存单个 Agent 的消息和工具调用上下文。

## 存储职责

| 存储 | 职责 |
|---|---|
| MySQL | 工作流定义、运行记录、步骤记录、审批记录和最终业务结果 |
| Redis Checkpointer | LangGraph 运行现场、状态快照和 `interrupt` 暂停点 |
| Redis Stream | 向前端实时推送节点、Token、工具和审批事件 |
| MongoDB | LLM 与工具调用的 Trace Span |

Checkpoint 不替代 MySQL。MySQL 仍然是业务事实来源，Redis 只负责恢复运行现场。

## 首次执行

创建 `multi_agent_runs` 记录时，将当时的工作流配置保存到
`workflow_config_json`。即使用户在审批等待期间修改了工作流，恢复时仍使用创建运行时的
配置，避免节点拓扑和 Checkpoint 不匹配。

```python
config = {
    "configurable": {
        "thread_id": f"workflow_run_{run_id}",
    }
}

await workflow_graph.ainvoke(initial_state, config=config)
```

## 审批暂停与恢复

工作流执行器遇到审批节点后，将恢复游标同步到 MySQL 和 `WorkflowRuntimeState`。生命周期图
进入审批节点并调用：

```python
decision = interrupt(approval_payload)
```

LangGraph 保存当前状态后结束本次后台任务。审批接口收到决定后，使用同一个 `thread_id`：

```python
await workflow_graph.ainvoke(
    Command(resume={"approved": True, "comment": "允许发布"}),
    config=config,
)
```

- 通过：恢复游标指向下一节点，继续执行。
- 拒绝：进入 `rejected` 终态并同步 MySQL、Redis Stream。

## Redis 要求

官方 `langgraph-checkpoint-redis` 依赖 RedisJSON 和 RediSearch。建议使用项目提供的 Redis
Stack 配置：

```bash
docker compose -f docker-compose.redis.yml up -d
```

该配置启用 AOF，并把数据保存在 Docker Volume。默认 Checkpoint 保留七天，可以通过以下
环境变量调整：

```bash
export WORKFLOW_CHECKPOINT_REDIS_URL="redis://127.0.0.1:6379/0"
export WORKFLOW_CHECKPOINT_TTL_MINUTES="10080"
```

如果当前 Redis 不支持所需模块或暂时不可连接，应用会输出明确警告并回退到
`InMemorySaver`，现有聊天和工作流功能仍可运行，但不具备跨进程恢复能力。

## 数据边界

State 中只保存恢复所需的轻量数据，不保存：

- API Key 和数据库密码；
- 数据库连接或 Redis 客户端；
- Agent 工具对象；
- 上传文件内容和宿主机绝对路径。

## 当前兼容策略

具体 DAG 遍历继续复用现有 `_walk_graph()`，外层生命周期由 StateGraph 管理。这种方式保持
条件分支、并行分支、SSE 和步骤持久化行为不变，同时先把人工审批迁移到原生
`interrupt/Command(resume)`。后续可以逐个将 DAG 节点转换为原生 StateGraph 节点，而不需要
再次修改持久化协议。
