# CrewAI 架构说明

## 1. 分层与所有权

平台采用 `Flow → Crew → Agent + Task` 四层结构。

### Agent

Agent 是可复用的专业成员，保存 CrewAI 的 `role`、`goal`、`backstory`、LLM、最大迭代次数以及 delegation、reasoning、planning、memory 等能力。Skill 和 MCP 永久挂载在 Agent 下，因为工具能力属于执行者，而不是某一次任务。

### Crew

Crew 是一次团队配置，包含成员 Agent、Task 和执行策略：

- `sequential`：任务顺序执行，Task 必须明确指定 Agent。
- `hierarchical`：Manager 负责协调，Task 可留空由其委派，也可指定非 Manager 成员。

### Task

Task 保存 description、expected output、负责 Agent、顺序、依赖、异步标记、Markdown 输出、重试次数和输出文件。

Task 的 `task_skills` 与 `task_mcps` 不是能力归属，只用于限制该任务可使用的 Agent 能力。某一类白名单为空时，该类不受限制。白名单中的能力必须已经挂载在负责人 Agent 下。

### Flow

Flow 是持久化的图执行器，通过节点和条件边串联一个或多个 Crew。它使用 CrewAI Crew 作为执行节点，但不是用 Python 装饰器声明的 CrewAI `Flow` 子类，这样页面上配置的图可以直接保存到数据库并动态执行。

## 2. 执行链

```text
用户消息
  → 校验 Crew/Flow 会话归属
  → 创建 trace_run
  → 构建 CrewAI LLM / Agent / Task / Crew
  → kickoff_async
  → 保存 crew/task/tool/flow_node spans
  → SSE 返回最终结果
  → 保存 assistant 消息并结束 Trace
```

Crew 使用 CrewAI 原生 `CrewStreamingOutput`，模型生成的文本以多个 SSE `chunk` 实时返回。协议同时发送 `status`（执行状态）、`phase_start`（Task 阶段切换）、`result`（最终结果）和 `done`（流结束）。多 Task 或多 Crew Flow 切换阶段时，前端会展示当前阶段，最终以 `result` 校准并持久化完整回答。

## 3. Flow 规则

- 起点：首个入度为 0 的节点。
- 分支：按 `priority` 从小到大匹配第一条满足条件的出边。
- 条件：`always`、`contains`、`equals`、`not_contains`。
- 防循环：单轮最多执行 `节点数 × 3` 步。
- `condition`：仅判断当前字符串状态。
- `transform`：支持 `config.prefix` 和 `config.suffix`。
- `approval`：记录 paused Span、返回待审批文本并停止；当前没有持久化恢复接口。
- `end`：立即返回当前状态。

## 4. 数据模型

| 表 | 作用 |
|---|---|
| `agents` | CrewAI Agent 定义 |
| `agent_skills` / `agent_mcps` | Agent 能力归属 |
| `crews` / `crew_agents` | 团队及成员 |
| `crew_tasks` | 持久化 Task |
| `task_dependencies` | Task context 依赖 |
| `task_skills` / `task_mcps` | 任务级能力白名单 |
| `flows` / `flow_nodes` / `flow_edges` | Flow 图 |
| `chat_sessions` | 绑定 `crew` 或 `flow` 的会话 |
| `trace_runs` / `trace_spans` | 每轮调用链 |

## 5. 配置注意事项

- Python 必须使用 3.11 环境，项目锁定 CrewAI `1.15.15`。
- `memory` 和部分 `planning` 场景可能触发 embedding 或额外 LLM 请求，默认关闭。
- 页面上的 `human_input` 当前作为预留配置保存，但运行时不会交给 CrewAI，以免 Web 服务阻塞等待控制台输入。
- `guardrail` 当前保存为说明文本，尚未转换为 CrewAI Python callable。
- 删除 Crew/Flow 会同步删除其会话和 Trace。被 Crew 使用的 Agent、被 Flow 使用的 Crew 不能直接删除，需先解除引用，避免留下不可运行的配置。

## 6. 后续增强方向

- Flow 审批任务表及 resume API。
- 可视化拖拽画布和图环检测。
- CrewAI 原生事件流与 token 级 SSE。
- Guardrail 函数注册中心。
- Memory 的 embedding 配置管理。
- Alembic 或专用 MySQL schema migration。
