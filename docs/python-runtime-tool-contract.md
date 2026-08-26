# Python Runtime 工具接口约定

本文记录 Agent Platform 中大模型调用 Python Runtime 的接口约定，包括：

- 发给大模型的工具定义；
- 大模型返回的工具调用；
- Runtime 的执行结果；
- 工具结果回传给大模型的消息；
- 文件上传、聊天请求和前端 SSE 事件。

对应实现：

- `backend/runtime/tools.py`
- `backend/core/agent_factory.py`
- `backend/services/runtime_service.py`
- `backend/runtime/child_runner.py`
- `backend/routers/runtime.py`
- `backend/routers/chat.py`

## 1. 调用流程

```text
用户消息
  -> LangGraph 将消息和工具定义发送给大模型
  -> 大模型返回 tool_calls（只生成工具名和参数）
  -> LangGraph 调用本地 StructuredTool
  -> API 将执行任务写入 Redis 队列
  -> Runtime Worker 在受限 Python 子进程中执行代码
  -> 工具结果作为 role=tool 消息回传给大模型
  -> 大模型根据执行结果生成最终回答
```

大模型本身不直接执行代码。代码由本项目的 Runtime Worker 执行。

## 2. 工具注册条件

只有同时满足以下条件，`ExecutePython` 和 `RunSkillScript` 才会注册到 Agent：

1. `PYTHON_RUNTIME_ENABLED=true`；
2. 创建 Agent Executor 时传入了 `RuntimeContext`。

聊天场景会传入：

```python
RuntimeContext(
    user_id=user["user_id"],
    session_id=session_id,
)
```

还需要单独启动 Runtime Worker：

```bash
python -m backend.runtime_worker
```

## 3. ExecutePython 工具

### 3.1 发给大模型的工具定义

LangChain 会将 `StructuredTool` 转换成当前模型供应商支持的工具格式。对于 OpenAI-compatible Chat Completions，等价结构如下：

```json
{
  "type": "function",
  "function": {
    "name": "ExecutePython",
    "description": "在受限的本地 Python Runtime 中执行代码。输入文件通过 INPUT_FILES 字典按文件 ID 获取，例如单文件时使用 file_path = next(iter(INPUT_FILES.values()))；不要猜测 /mnt/data 等文件路径。只允许向 OUTPUT_DIR 写文件；将最终 JSON 赋值给 result，生成文件写入 OUTPUT_DIR。",
    "parameters": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "需要执行的完整 Python 代码"
        },
        "input_file_ids": {
          "type": "array",
          "items": { "type": "string" },
          "default": [],
          "description": "代码需要读取的 Runtime 文件 ID 列表"
        },
        "timeout_seconds": {
          "type": "integer",
          "minimum": 1,
          "maximum": 120,
          "default": 60,
          "description": "执行超时秒数"
        }
      },
      "required": ["code"]
    }
  }
}
```

### 3.2 大模型返回的工具调用

OpenAI-compatible 原始响应示例：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "ExecutePython",
        "arguments": "{\"code\":\"result = {'answer': 1 + 2}\",\"input_file_ids\":[],\"timeout_seconds\":60}"
      }
    }
  ]
}
```

`function.arguments` 是一个 JSON 字符串，不是直接嵌套的 JSON 对象。

LangChain 通常将其规范化为：

```python
AIMessage(
    content="",
    tool_calls=[{
        "name": "ExecutePython",
        "args": {
            "code": "result = {'answer': 1 + 2}",
            "input_file_ids": [],
            "timeout_seconds": 60,
        },
        "id": "call_abc123",
        "type": "tool_call",
    }],
)
```

### 3.3 Python 代码运行环境

执行代码可以使用以下预置变量：

| 变量 | 类型 | 说明 |
|---|---|---|
| `INPUT_DIR` | `str` | 本次执行的输入目录 |
| `OUTPUT_DIR` | `str` | 唯一允许写入生成文件的目录 |
| `INPUT_FILES` | `dict[str, str]` | Runtime 文件 ID 到实际输入路径的映射 |
| `RUNTIME_ARGS` | `dict` | `RunSkillScript` 接收的业务参数；动态代码通常为空对象 |

读取上传文件并生成 Excel 的示例：

```python
from pathlib import Path
import openpyxl

input_path = next(iter(INPUT_FILES.values()))
workbook = openpyxl.load_workbook(input_path)
sheet = workbook.active

result = {
    "sheet": sheet.title,
    "rows": sheet.max_row,
    "columns": sheet.max_column,
}

output_path = Path(OUTPUT_DIR) / "result.xlsx"
workbook.save(output_path)
```

重要约定：

- 最终结构化结果必须赋值给全局变量 `result`；
- 生成文件必须写入 `OUTPUT_DIR`；
- 输入文件应通过 `INPUT_FILES` 获取，不能猜测宿主机路径；
- Runtime 禁止网络、子进程和工作目录外文件访问；
- 当前允许导入的主要数据处理模块包括 `csv`、`json`、`numpy`、`pandas`、`openpyxl`、`matplotlib`、`docx` 和 `pypdf`。

### 3.4 ExecutePython 执行结果

成功或运行期失败的完整结果：

```json
{
  "executionId": "4ce7e98d-0000-0000-0000-000000000000",
  "status": "completed",
  "exitCode": 0,
  "stdout": "",
  "stderr": "",
  "error": "",
  "result": {
    "answer": 3
  },
  "artifacts": [
    {
      "fileId": "file-id",
      "name": "result.xlsx",
      "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 18234,
      "url": "/api/runtime/files/file-id"
    }
  ]
}
```

`status` 的取值：

| 状态 | 含义 |
|---|---|
| `completed` | 子进程正常结束 |
| `failed` | Python 异常、Worker 不可用或调度失败 |
| `timed_out` | 超过执行时间限制 |
| `rejected` | 代码在执行前被安全策略拒绝 |

执行前被拒绝时，工具返回简化结构：

```json
{
  "status": "rejected",
  "error": "不允许导入模块：subprocess"
}
```

## 4. RunSkillScript 工具

`RunSkillScript` 只允许执行已经绑定到当前 Agent 的 Skill 包内的 `.py` 文件。

### 4.1 发给大模型的工具定义

```json
{
  "type": "function",
  "function": {
    "name": "RunSkillScript",
    "description": "执行已激活 Skill 包内的 Python 脚本。脚本通过 INPUT_FILES、OUTPUT_DIR 和 RUNTIME_ARGS 获取输入，不允许执行未绑定 Skill 的脚本。",
    "parameters": {
      "type": "object",
      "properties": {
        "skill_name": {
          "type": "string",
          "description": "已经激活的 Skill 名称"
        },
        "script_path": {
          "type": "string",
          "description": "Skill 目录内的 .py 脚本相对路径"
        },
        "arguments": {
          "type": "object",
          "default": {},
          "description": "通过 RUNTIME_ARGS 传给脚本的参数"
        },
        "input_file_ids": {
          "type": "array",
          "items": { "type": "string" },
          "default": [],
          "description": "脚本需要读取的 Runtime 文件 ID 列表"
        },
        "timeout_seconds": {
          "type": "integer",
          "minimum": 1,
          "maximum": 120,
          "default": 60,
          "description": "执行超时秒数"
        }
      },
      "required": ["skill_name", "script_path"]
    }
  }
}
```

### 4.2 模型调用示例

```json
{
  "id": "call_skill_001",
  "type": "function",
  "function": {
    "name": "RunSkillScript",
    "arguments": "{\"skill_name\":\"Excel分析\",\"script_path\":\"scripts/analyze.py\",\"arguments\":{\"sheet\":\"销售明细\"},\"input_file_ids\":[\"file-id\"],\"timeout_seconds\":60}"
  }
}
```

执行结果与 `ExecutePython` 使用相同结构。

## 5. 工具结果回传模型

执行完成后，结果会关联原始 `tool_call_id`，再作为工具消息交给模型：

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "{\"executionId\":\"4ce7e98d-...\",\"status\":\"completed\",\"exitCode\":0,\"stdout\":\"\",\"stderr\":\"\",\"error\":\"\",\"result\":{\"answer\":3},\"artifacts\":[]}"
}
```

模型随后生成普通助手消息：

```json
{
  "role": "assistant",
  "content": "代码执行完成，计算结果是 3。"
}
```

## 6. Runtime 文件 HTTP 接口

所有接口都需要：

```http
Authorization: Bearer <token>
```

### 6.1 上传输入文件

```http
POST /api/runtime/files
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | File | 是 | Runtime 输入文件，默认最大 20 MB |
| `session_id` | Integer | 否 | 绑定的聊天会话 ID |

成功响应：

```json
{
  "id": "fb0901ac-0000-0000-0000-000000000000",
  "name": "sales.xlsx",
  "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "size": 18234,
  "kind": "runtime_file"
}
```

### 6.2 携带文件发起聊天

```http
POST /api/chat/stream
Content-Type: application/json
```

请求体：

```json
{
  "message": "分析这个 Excel 的销售数据",
  "session_id": 123,
  "images": [],
  "file_ids": [
    "fb0901ac-0000-0000-0000-000000000000"
  ]
}
```

约束：

- `message` 必须是非空字符串；
- `session_id` 必须是整数；
- `file_ids` 必须是字符串数组，单次最多 10 个；
- 后端会验证文件属于当前用户。

响应为 `text/event-stream`。

### 6.3 下载输入文件或生成文件

```http
GET /api/runtime/files/{file_id}
```

成功时返回文件二进制流，并通过 `Content-Disposition` 提供文件名。

常见错误：

| HTTP 状态码 | 含义 |
|---|---|
| `400` | 上传文件不合法、文件过大或参数格式错误 |
| `401` | 未登录或 token 失效 |
| `404` | 会话或文件不存在，或者不属于当前用户 |
| `410` | 数据库记录存在，但磁盘文件已经丢失 |
| `429` | 同一会话已有生成任务正在运行 |

## 7. 前端 SSE 事件

聊天接口通过 SSE 向前端发送以下事件：

### 工具开始

```text
data:{"type":"tool_start","content":"{\"name\":\"ExecutePython\",\"input\":\"{...}\"}"}
```

其中 `content` 自身也是 JSON 字符串。当前后端会将工具输入截断到 200 个字符。

### 工具结束

```text
data:{"type":"tool_end","content":"{\"status\":\"completed\",...}"}
```

当前后端会将展示用的工具结果截断到 500 个字符；完整结果仍会在 Agent 内部交给模型。

其他事件：

| `type` | 含义 |
|---|---|
| `thinking` | 工具调用前的模型文本 |
| `chunk` | 最终回答文本片段 |
| `reclassify` | 前端重新归类 thinking/answer |
| `tool_start` | 工具开始执行 |
| `tool_end` | 工具执行结束 |
| `error` | 执行或生成失败 |
| `done` | 本轮流结束 |

## 8. 安全边界

当前 Runtime 包含以下限制：

- AST 静态检查和允许导入模块名单；
- 禁止 `eval`、`exec`、`compile`、`__import__` 等调用；
- 独立 Python 子进程；
- 隔离模式 `python -I`；
- CPU、内存、运行时间和输出大小限制；
- 禁止网络和创建子进程；
- 只允许读取本次执行目录及 Python 运行库；
- 只允许写入 `OUTPUT_DIR`；
- 文件 ID 按当前用户校验。

这些限制适合本地开发，但不应视为完整的不可信代码安全边界。生产环境建议将 Worker 放入独立容器、gVisor 或虚拟机。

## 9. 当前注意事项

1. `PYTHON_RUNTIME_ENABLED` 默认是 `true`，但仍必须启动 Redis 和 `backend.runtime_worker`。
2. 项目 `backend/.venv` 当前使用 Python 3.8，而部分代码使用 `set[str]` 等 Python 3.9+ 语法；应升级到 Python 3.11，或改为兼容写法。
3. 普通 Runtime 文件保存在消息附件中，但模型消息构建逻辑需要确保将文件 ID 和文件名明确加入上下文，否则模型无法可靠填写 `input_file_ids`。
4. `tool_start` 和 `tool_end` SSE 是前端展示协议，不是模型供应商的原始 tool-calling 协议。

