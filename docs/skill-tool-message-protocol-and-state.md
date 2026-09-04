# Skill 工具交互消息协议与 LangGraph State

## 1. 文档目标

本文说明 Agent Platform 中 Agent 读取 Skill 时的真实交互过程，重点描述：

1. 每次请求大模型时发送的 `messages` 和 `tools` 格式；
2. 大模型返回给 Agent 的 `content` 和 `tool_calls` 格式；
3. LangChain 如何将返回值转换成 `AIMessage`；
4. Skill 执行结果如何转换成 `ToolMessage`；
5. 当前项目是否使用了 LangGraph State，以及 State 如何变化。

本文示例采用 OpenAI-compatible Chat Completions 等价格式。项目代码使用 `ChatOpenAI + create_react_agent`，实际 JSON 由 LangChain 根据模型供应商自动生成，不是业务代码手工拼接。

对应实现：

- `backend/core/tools.py`
- `backend/core/agent_factory.py`
- `backend/core/streaming.py`
- `backend/services/chat_service.py`

## 2. 当前项目中的 Skill 工具定义

绑定 Skill 后，项目会向 Agent 注册两个基础工具：

- `Skill`：根据 Skill 名称读取入口文件 `SKILL.md`；
- `SkillFile`：读取 `SKILL.md` 引用的 Skill 包内文本文件。

假设当前 Agent 绑定了以下 Skill：

```text
名称：Excel分析
描述：读取 Excel 文件，统计数据并生成分析结果
```

### 2.1 Skill 工具定义

发送给 OpenAI-compatible 模型的等价定义如下：

```json
{
  "type": "function",
  "function": {
    "name": "Skill",
    "description": "Execute a skill within the main conversation.\n<available_skills>\n<skill>\n  <name>Excel分析</name>\n  <description>读取 Excel 文件，统计数据并生成分析结果</description>\n</skill>\n</available_skills>\n\nInvoke a skill by its name to get full instructions and context for the task.",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {
          "type": "string",
          "description": "要执行的技能名称"
        }
      },
      "required": ["command"]
    }
  }
}
```

### 2.2 SkillFile 工具定义

```json
{
  "type": "function",
  "function": {
    "name": "SkillFile",
    "description": "Read a UTF-8 text file referenced by a Skill, such as references/guide.md. Call Skill first, then read only files it references.",
    "parameters": {
      "type": "object",
      "properties": {
        "skill_name": {
          "type": "string",
          "description": "所属的技能名称"
        },
        "path": {
          "type": "string",
          "description": "技能包内的相对路径"
        }
      },
      "required": ["skill_name", "path"]
    }
  }
}
```

每次调用大模型时都需要再次携带可用的 `tools`。大模型接口本身是无状态的，不能假设第二次请求还记得第一次传入的工具定义。

## 3. 第一轮：模型决定读取 SKILL.md

用户发送：

```text
请分析我上传的销售 Excel，并按地区汇总销售额。
```

### 3.1 Agent 第一次请求大模型

等价请求：

```json
{
  "model": "模型名称",
  "messages": [
    {
      "role": "system",
      "content": "你是一名数据分析 Agent。处理任务前应先读取匹配的 Skill。"
    },
    {
      "role": "user",
      "content": "[当前日期：2026-09-02] 请分析我上传的销售 Excel，并按地区汇总销售额。"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "Skill",
        "description": "包含当前 Agent 已绑定 Skill 列表的工具说明",
        "parameters": {
          "type": "object",
          "properties": {
            "command": {
              "type": "string",
              "description": "要执行的技能名称"
            }
          },
          "required": ["command"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "SkillFile",
        "description": "读取 Skill 引用的 UTF-8 文本文件",
        "parameters": {
          "type": "object",
          "properties": {
            "skill_name": {"type": "string"},
            "path": {"type": "string"}
          },
          "required": ["skill_name", "path"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

说明：项目可能同时传递 MCP、HTTP Action、`ExecutePython` 等其他工具。这里为了突出 Skill 读取流程，只展示 `Skill` 和 `SkillFile`。

### 3.2 大模型第一次返回

模型判断需要使用“Excel分析”Skill，于是返回工具调用：

```json
{
  "id": "chatcmpl-round-1",
  "choices": [
    {
      "index": 0,
      "finish_reason": "tool_calls",
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_skill_001",
            "type": "function",
            "function": {
              "name": "Skill",
              "arguments": "{\"command\":\"Excel分析\"}"
            }
          }
        ]
      }
    }
  ]
}
```

关键字段：

| 字段 | 含义 |
|---|---|
| `finish_reason=tool_calls` | 本轮没有给最终答案，需要执行工具 |
| `tool_calls[].id` | 本次工具调用 ID，工具结果必须使用它关联 |
| `function.name` | 要调用的工具名称 |
| `function.arguments` | JSON 字符串形式的工具参数 |

LangChain 会将模型响应转换为：

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "Skill",
            "args": {"command": "Excel分析"},
            "id": "call_skill_001",
            "type": "tool_call",
        }
    ],
)
```

这里的 `name/args/id` 就是大模型返回给 Agent 的主要调用参数。

## 4. Agent 执行 Skill 工具

LangGraph 根据 `tool_calls` 找到项目注册的 `Skill` 工具，执行：

```python
# command 来自大模型返回的 arguments。
execute_skill(command="Excel分析")
```

项目随后读取该 Skill 的 `SKILL.md`。假设文件内容为：

```markdown
# Excel 分析

1. 先读取 `references/excel-guide.md`。
2. 使用 ExecutePython 和 openpyxl 分析工作簿。
3. 汇总结果必须包含地区、销售额和占比。
```

LangGraph 将执行结果包装成：

```python
ToolMessage(
    content="# Excel 分析\n\n1. 先读取 `references/excel-guide.md`。\n2. 使用 ExecutePython 和 openpyxl 分析工作簿。\n3. 汇总结果必须包含地区、销售额和占比。",
    name="Skill",
    tool_call_id="call_skill_001",
)
```

注意：这段内容是项目执行工具后产生的，不是大模型返回的。

## 5. 第二轮：模型决定读取 SkillFile

### 5.1 Agent 第二次请求大模型

第二次请求必须携带第一轮 Assistant 工具调用和对应 Tool 结果：

```json
{
  "model": "模型名称",
  "messages": [
    {
      "role": "system",
      "content": "你是一名数据分析 Agent。处理任务前应先读取匹配的 Skill。"
    },
    {
      "role": "user",
      "content": "[当前日期：2026-09-02] 请分析我上传的销售 Excel，并按地区汇总销售额。"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_skill_001",
          "type": "function",
          "function": {
            "name": "Skill",
            "arguments": "{\"command\":\"Excel分析\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_skill_001",
      "name": "Skill",
      "content": "# Excel 分析\n\n1. 先读取 `references/excel-guide.md`。\n2. 使用 ExecutePython 和 openpyxl 分析工作簿。\n3. 汇总结果必须包含地区、销售额和占比。"
    }
  ],
  "tools": [
    {"type": "function", "function": {"name": "Skill", "description": "...", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "SkillFile", "description": "...", "parameters": {"type": "object", "properties": {"skill_name": {"type": "string"}, "path": {"type": "string"}}, "required": ["skill_name", "path"]}}}
  ],
  "tool_choice": "auto"
}
```

### 5.2 大模型第二次返回

模型遵循 `SKILL.md` 指令，继续调用 `SkillFile`：

```json
{
  "choices": [
    {
      "finish_reason": "tool_calls",
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_skill_file_001",
            "type": "function",
            "function": {
              "name": "SkillFile",
              "arguments": "{\"skill_name\":\"Excel分析\",\"path\":\"references/excel-guide.md\"}"
            }
          }
        ]
      }
    }
  ]
}
```

对应的 LangChain 对象：

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "SkillFile",
            "args": {
                "skill_name": "Excel分析",
                "path": "references/excel-guide.md",
            },
            "id": "call_skill_file_001",
            "type": "tool_call",
        }
    ],
)
```

## 6. Agent 执行 SkillFile 工具

项目执行：

```python
# 只能读取 Skill 包目录内经过路径校验的文本文件。
execute_skill_file(
    skill_name="Excel分析",
    path="references/excel-guide.md",
)
```

假设返回：

```markdown
读取工作簿时优先使用 openpyxl；公式单元格需要同时检查公式和值；不要一次把全部工作表内容发送给模型。
```

对应的工具消息：

```json
{
  "role": "tool",
  "tool_call_id": "call_skill_file_001",
  "name": "SkillFile",
  "content": "读取工作簿时优先使用 openpyxl；公式单元格需要同时检查公式和值；不要一次把全部工作表内容发送给模型。"
}
```

## 7. 第三轮：模型决定下一步或返回最终答案

第三次模型请求的 `messages` 会按顺序包含：

```text
SystemMessage
HumanMessage
AIMessage：调用 Skill
ToolMessage：SKILL.md 内容
AIMessage：调用 SkillFile
ToolMessage：引用文件内容
```

如果任务还需要执行 Python，模型会继续返回：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_python_001",
      "type": "function",
      "function": {
        "name": "ExecutePython",
        "arguments": "{\"code\":\"...\",\"input_file_ids\":[\"file-id\"],\"timeout_seconds\":30}"
      }
    }
  ]
}
```

如果已经可以回答，模型返回普通 Assistant 消息：

```json
{
  "choices": [
    {
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "已按照 Excel 分析 Skill 的要求完成处理，以下是按地区汇总的销售结果……"
      }
    }
  ]
}
```

## 8. 当前项目有没有体现 LangChain/LangGraph State

有。项目最初只使用 `create_react_agent` 内置的隐式消息 State；当前已经新增
`AgentPlatformState`，在保留内置 `messages/remaining_steps` 的基础上扩展平台业务字段。

项目调用 Graph 时传入：

```python
# messages 是当前 Graph State 的核心字段。
await agent_executor.astream_events(
    {"messages": messages},
    config={
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_tool_rounds * 2 + 5,
    },
    version="v2",
)
```

这里的：

```python
{"messages": messages}
```

就是传给 LangGraph 的初始 State。

### 8.1 Skill 调用过程中的 State 变化

初始 State：

```python
{
    "messages": [
        HumanMessage(content="请分析销售 Excel")
    ]
}
```

模型决定调用 Skill 后：

```python
{
    "messages": [
        HumanMessage(content="请分析销售 Excel"),
        AIMessage(
            content="",
            tool_calls=[{
                "name": "Skill",
                "args": {"command": "Excel分析"},
                "id": "call_skill_001",
            }],
        ),
    ]
}
```

Skill 工具执行完成后：

```python
{
    "messages": [
        HumanMessage(content="请分析销售 Excel"),
        AIMessage(tool_calls=[...]),
        ToolMessage(
            content="SKILL.md 的完整内容",
            tool_call_id="call_skill_001",
        ),
    ]
}
```

读取 SkillFile 后：

```python
{
    "messages": [
        HumanMessage(content="请分析销售 Excel"),
        AIMessage(tool_calls=[Skill]),
        ToolMessage(content="SKILL.md 内容"),
        AIMessage(tool_calls=[SkillFile]),
        ToolMessage(content="references/excel-guide.md 内容"),
    ]
}
```

最终回答后：

```python
{
    "messages": [
        HumanMessage(...),
        AIMessage(tool_calls=[Skill]),
        ToolMessage(...),
        AIMessage(tool_calls=[SkillFile]),
        ToolMessage(...),
        AIMessage(content="最终回答"),
    ]
}
```

这就是项目中最明显的 LangGraph State 表现：`messages` 会在 Agent 节点与 Tool 节点之间持续追加。

### 8.2 Checkpoint 与 State 的关系

项目将全局 `InMemorySaver` 传给 `create_react_agent`，并在每次执行时传入 `thread_id`。LangGraph 会按 `thread_id` 保存该 State 的阶段性快照。

聊天使用：

```text
session_{session_id}_message_{user_message_id}
```

工作流步骤使用：

```text
workflow_{workflow_id}_run_{run_id}_step_{step_order}
```

因此：

- State 是当前图执行中的数据；
- Checkpoint 是 State 在不同执行步骤后的快照；
- `thread_id` 是 Checkpoint 状态链的隔离键。

### 8.3 当前自定义 State

项目已经显式定义：

```python
class AgentPlatformState(AgentState):
    runtime_file_ids: NotRequired[list[str]]
    available_skills: NotRequired[list[str]]
    loaded_skills: NotRequired[list[str]]
    current_input: NotRequired[str]
    current_node_id: NotRequired[str | None]
    structured_result: NotRequired[dict]
    approval_status: NotRequired[str]
    error: NotRequired[str]
```

当前已经进入 State 的数据包括：

- 当前 Runtime 文件 ID；
- 当前 Agent 可用的 Skill 名称；
- 当前输入和工作流 Agent 节点 ID；
- 已解析的结构化输出；
- 为后续扩展预留的已加载 Skill、审批状态和错误字段。

用户 ID、数据库连接和工具实例等不随节点变化的运行依赖仍保留在 `RuntimeContext`
或服务层中，避免敏感数据进入 Checkpoint。人工审批仍由现有 MySQL 工作流机制负责，
本次改造没有改变审批协议。

## 9. 当前 State 的持久化边界

当前聊天使用“每条用户消息一个新 `thread_id`”，并在每轮开始时从 MySQL恢复历史 `user/assistant` 消息。

这意味着：

- 同一次用户请求内，Skill、SkillFile、MCP 和 Python Tool 的调用消息保存在 State 中；
- 下一次用户请求不会复用上一次 State；
- MySQL 当前主要持久化用户消息和最终 Assistant 回答；
- 中间的 Skill Tool Call、Skill 内容和 ToolMessage 不会作为长期聊天历史完整恢复；
- 服务重启后长期记忆来自 MySQL，不是 `InMemorySaver`。

所以当前项目已经形成“自定义业务 State + 内存 Checkpoint”的基础架构，但尚未切换到
持久化 Checkpointer，也没有把整个工作流改写成原生 `StateGraph`。

## 10. 建议的后续实现方案

当前项目已经采用以下兼容式状态结构：

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentPlatformState(AgentState):
    runtime_file_ids: NotRequired[list[str]]
    available_skills: NotRequired[list[str]]
    loaded_skills: NotRequired[list[str]]
    current_input: NotRequired[str]
    current_node_id: NotRequired[str | None]
    structured_result: NotRequired[dict]
    approval_status: NotRequired[str]
    error: NotRequired[str]
```

后续建议实施顺序：

1. 让 Skill 工具通过 State-aware Tool 更新 `loaded_skills`；
2. 为并行分支结果设计明确的 Reducer；
3. 使用持久化 Checkpointer 后再引入跨请求稳定 `thread_id`；
4. 明确 MySQL 与 Checkpoint 的唯一事实来源和同步策略；
5. 最后再实现 LangGraph 原生 `interrupt/resume` 审批。
