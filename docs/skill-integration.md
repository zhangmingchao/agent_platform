# Skill 集成实现方式详解

> 从工具构建到 Agent-LLM 交互，完整解析 Skill 在 Agent 平台中的运作机制与入参出参。

## 一、概述

Skill 是 Agent 平台中用户自定义的能力扩展单元。一个 Skill 就是一个功能包，包含使用说明（SKILL.md）、可选的动作清单（skill.json）和相关参考文件。

大模型并非"直接读取 Skill 文件"，而是通过 **LangChain 工具调用** 的方式间接操作 Skill。平台将每个 Skill 的能力转化为标准化的 LangChain StructuredTool，注入到 LangGraph ReAct Agent 的工具列表中，由 LLM 根据任务自主决定调用哪个工具。

> **核心设计思想：** Skill 的内容对 LLM 来说是黑盒，LLM 通过工具接口与 Skill 交互。平台负责将 Skill 的声明式定义（SKILL.md + skill.json）转化为可被 LLM 理解和调用的工具集。

## 二、架构设计

Skill 集成采用"三层工具模型"：文档读取类工具 + 文件读取工具 + HTTP 动作工具。三类工具各司其职，覆盖了 Skill 的全部使用场景。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│              "北京今天天气怎么样？"                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Agent 层                              │
│            ┌──────────────────────────────┐                 │
│            │     LangGraph ReAct Agent    │                 │
│            │                              │                 │
│            │  ┌────────────────────────┐  │                 │
│            │  │     大模型 LLM         │  │                 │
│            │  └────────────────────────┘  │                 │
│            └──────────────┬───────────────┘                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Skill 工具层 (LangChain StructuredTool)         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Skill 工具   │  │ SkillFile 工具 │  │ HTTP Action 工具  │   │
│  │ 读SKILL.md   │  │ 读包内参考文件 │  │  执行外部API调用  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Skill 数据层                              │
│                                                             │
│    ┌──────────┐     ┌──────────────┐     ┌───────────┐      │
│    │ SKILL.md │     │ references/  │     │ skill.json│      │
│    │ 技能说明  │     │ 参考文档     │     │ 动作清单   │      │
│    └──────────┘     └──────────────┘     └─────┬─────┘      │
└────────────────────────────────────────────────┼────────────┘
                                                 │
                                                 ▼
                                       ┌──────────────────┐
                                       │   第三方 API     │
                                       │ 天气/订单/...    │
                                       └──────────────────┘
```

## 三、三类 Skill 工具

每个 Skill 最多会向 Agent 注入以下三类工具，由 `build_skill_tools()` 函数统一构建：

| 工具 | 图标 | 工具名 | 作用 |
|------|------|--------|------|
| 技能主文档读取 | 📘 | `Skill` | 读取 SKILL.md 全文，获取技能使用说明 |
| 包内文件读取 | 📄 | `SkillFile` | 读取 Skill 包内的其他参考文件，带路径越界校验 |
| HTTP Action 工具 | 🌐 | 动态生成 | 从 skill.json 的 tools 数组动态生成，每个 action 独立成工具 |

> **注意：** HTTP Action 工具是可选的。只有当 Skill 包中存在 `skill.json` 且包含 `tools` 数组时，才会生成对应的 Action 工具。没有 skill.json 的 Skill 只有 Skill 和 SkillFile 两个工具。

### 3.1 Skill 工具

- **工具名：** `Skill`
- **入参：** `command: string` — 要执行的技能名称
- **功能：** 读取指定 Skill 的 `SKILL.md` 全文，返回给 LLM。LLM 通过阅读 SKILL.md 了解该技能的使用方法、输入输出格式和操作步骤。
- **典型场景：** LLM 第一次接触某个 Skill 时，先调用 `Skill` 工具读说明书，再根据说明书决定后续操作。

### 3.2 SkillFile 工具

- **工具名：** `SkillFile`
- **入参：**
  - `skill_name: string` — 所属技能名称
  - `path: string` — 技能包内的相对路径
- **功能：** 读取 Skill 包内指定路径的文本文件。用于 SKILL.md 中引用的参考文档、模板文件等。
- **安全控制：** `_resolve_skill_file()` 做严格的路径越界校验，确保只能读取 Skill 目录内的文件。

### 3.3 HTTP Action 工具

- **工具名：** 由 `skill.json` 中 `tools[].name` 动态决定（如 `query_weather`）
- **入参：** 由 `parameters` 字段动态生成 Pydantic Schema
- **功能：** 每个声明的 HTTP action 独立成为一个 LangChain 工具，LLM 调用时直接发起 HTTP 请求。
- **支持的 HTTP 方法：** GET、POST、PUT、PATCH、DELETE
- **URL 参数渲染：** 支持 `{paramName}` 占位符，调用时自动替换为参数值，剩余参数作为 query params（GET）或 JSON body（其他方法）。

## 四、工具构建流程

Agent 实例创建时，会从数据库加载关联的 Skill 列表，然后通过以下流程构建全部工具：

```
chat_service.py          skill_service.py          agent_factory.py          tools.py           skill_actions.py          MySQL         文件系统
      │                       │                        │                      │                      │                 │              │
      │ get_agent_skills()    │                        │                      │                      │                 │              │
      │──────────────────────>│                        │                      │                      │                 │              │
      │                       │ SELECT s.* FROM skills │                      │                      │                 │              │
      │                       │ JOIN agent_skills     │                      │                      │                 │              │
      │                       │──────────────────────────────────────────────────────────────────>│                 │              │
      │                       │<──────────────────────────────────────────────────────────────────│                 │              │
      │                       │ skills 列表            │                      │                      │                 │              │
      │                       │                        │                      │                      │                 │              │
      │                循环每个 skill:                 │                      │                      │                 │              │
      │                       │ read_skill_entrypoint()│                      │                      │                 │              │
      │                       │────────────────────────────────────────────────────────────────────────────────────>│              │
      │                       │<────────────────────────────────────────────────────────────────────────────────────│              │
      │                       │ SKILL.md 内容          │                      │                      │                 │              │
      │<──────────────────────│                        │                      │                      │                 │              │
      │ skills 数据           │                        │                      │                      │                 │              │
      │                       │                        │                      │                      │                 │              │
      │ create_agent_instance(agent, skills, ...)     │                      │                      │                 │              │
      │──────────────────────────────────────────────>│                      │                      │                 │              │
      │                       │                        │ build_all_tools()    │                      │                 │              │
      │                       │                        │─────────────────────>│                      │                 │              │
      │                       │                        │                      │ build_skill_tools()  │                      │              │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │                      │ ── 构建 Skill 工具 ── │                      │              │
      │                       │                        │                      │ ── 构建 SkillFile 工具 │                      │              │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │                      │ build_skill_action_tools(skills)              │              │
      │                       │                        │                      │─────────────────────>│                      │              │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │                      │                循环每个 skill:            │              │
      │                       │                        │                      │                      │ read_skill_action_manifest() │          │
      │                       │                        │                      │                      │───────────────────────────────────>│    │
      │                       │                        │                      │                      │<───────────────────────────────────│    │
      │                       │                        │                      │                      │ skill.json 内容   │              │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │                      │                循环每个 action:           │              │
      │                       │                        │                      │                      │ _normalize_action() 校验            │
      │                       │                        │                      │                      │ _create_args_schema() 动态生成Pydantic│
      │                       │                        │                      │                      │ StructuredTool.from_function()      │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │                      │<─────────────────────│ HTTP Action 工具列表  │              │
      │                       │                        │                      │                      │                      │              │
      │                       │                        │<─────────────────────│ [Skill, SkillFile, ...actions]         │              │
      │                       │                        │ create_react_agent(llm, tools) │                      │                 │              │
      │                       │                        │                      │                      │                 │              │
      │<──────────────────────────────────────────────│ agent_executor       │                      │                 │              │
```

**步骤分解：**

1. **加载 Skill 数据：** `chat_service.prepare_chat_run()` 调用 `get_agent_skills()`，从 `agent_skills` 关联表查询 Agent 绑定的所有 Skill，并读取 SKILL.md 内容。
2. **构建 Skill + SkillFile 工具：** `build_skill_tools()` 创建两个基础工具，用于读取 SKILL.md 和包内其他文件。
3. **构建 HTTP Action 工具：** `build_skill_action_tools()` 读取每个 Skill 的 `skill.json`，遍历 `tools` 数组，为每个 action 动态生成一个 StructuredTool。
4. **注入 Agent：** 全部工具合并后传入 `create_react_agent()`，LLM 就能在推理过程中按需调用这些 Skill 工具了。

## 五、Agent-LLM 交互模拟（读取 Skill 场景）

以下以"数据分析 Skill"为例，完整模拟 LLM 通过 `Skill` 工具读取 SKILL.md、再通过 `SkillFile` 读取参考文件、最后执行操作的完整交互过程。重点展示每一轮 LLM 请求的 **messages 入参格式** 和 **AIMessage 出参格式**。

> **场景设定：** Agent 绑定了一个名为 "data_analysis" 的 Skill（数据分析技能），Skill 包内有 SKILL.md（使用说明）和 references/cheatsheet.md（函数速查表）。用户上传了一个 Excel 文件，让 Agent 用数据分析技能处理。
>
> **可用工具：** `Skill`、`SkillFile`、`ExecutePython`（Runtime 工具，用于执行代码）

### 5.1 初始状态：工具列表

Agent 创建完成后，LLM 可调用的工具列表（Skill 相关部分）：

| 工具名 | 入参 Schema | 描述 |
|--------|-------------|------|
| `Skill` | `{ command: string }` | 读取指定 Skill 的 SKILL.md 全文 |
| `SkillFile` | `{ skill_name: string, path: string }` | 读取 Skill 包内的参考文件 |
| `ExecutePython` | `{ code: string }` | 在沙箱中执行 Python 代码 |

---

### 5.2 第一轮：LLM 决定调用 Skill 工具读说明书

#### 入参：LangGraph 发给 LLM 的完整请求（messages + tools）

```json
{
  "messages": [
    {
      "role": "system",
      "content": "你是一个智能助手，能够调用工具来完成任务。"
    },
    {
      "role": "human",
      "content": "[当前日期：2026-09-01] 用数据分析技能帮我统计一下这个 Excel 文件的基本信息：行数、列名、数据类型。文件ID: file_abc123"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "Skill",
        "description": "Execute a skill within the main conversation.\n<available_skills>\n<skill>\n  <name>data_analysis</name>\n  <description>数据分析技能，提供数据清洗、统计、可视化等能力</description>\n</skill>\n</available_skills>\n\nInvoke a skill by its name to get full instructions and context for the task.",
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
        "description": "Read a UTF-8 text file referenced by a Skill, such as references/guide.md. Call Skill first, then read only files it references.",
        "parameters": {
          "type": "object",
          "properties": {
            "skill_name": { "type": "string", "description": "所属的技能名称" },
            "path": { "type": "string", "description": "技能包内的相对路径" }
          },
          "required": ["skill_name", "path"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "ExecutePython",
        "description": "在受限的 Python 沙箱中执行代码...",
        "parameters": {
          "type": "object",
          "properties": {
            "code": { "type": "string" }
          },
          "required": ["code"]
        }
      }
    }
  ]
}
```

> 关键点：`Skill` 工具的 description 里用 XML 格式列出了所有可用 Skill 的名称和描述，LLM 从这里知道有哪些 Skill 可以调用。

#### 出参：LLM 返回（决定调用 Skill 工具）

```json
{
  "role": "ai",
  "content": "好的，我先查看数据分析技能的使用说明。",
  "tool_calls": [
    {
      "id": "call_001",
      "name": "Skill",
      "args": {
        "command": "data_analysis"
      }
    }
  ]
}
```

> LLM 看到用户提到"数据分析技能"，同时工具列表中有 `Skill` 工具且可用技能包含 `data_analysis`，因此调用 `Skill(command="data_analysis")` 来读取说明书。

---

### 5.3 第二轮：Skill 工具返回 SKILL.md 内容

#### 工具执行过程

```python
# backend/core/tools.py · execute_skill()
def execute_skill(command: str) -> str:
    skill = skills_map.get(command)           # 按名称查找 Skill
    content = read_skill_entrypoint(skill["id"], skill.get("content", ""))
    return content                             # 返回 SKILL.md 全文
```

**SKILL.md 内容（简化示例）：**
```markdown
# 数据分析技能

## 概述
本技能提供数据清洗、统计分析和可视化能力。

## 使用流程
1. 使用 pandas 读取数据文件（通过 INPUT_FILES 获取路径）
2. 先调用 info() 查看基本信息
3. 根据需求进行数据处理
4. 将结果赋值给 result 变量，格式为 JSON

## 参考文件
- references/cheatsheet.md — pandas 常用函数速查表
```

#### 出参：ToolMessage（追加到 messages，作为第 4 条）

```json
{
  "role": "tool",
  "tool_call_id": "call_001",
  "content": "# 数据分析技能\n\n## 概述\n本技能提供数据清洗、统计分析和可视化能力。\n\n## 使用流程\n1. 使用 pandas 读取数据文件（通过 INPUT_FILES 获取路径）\n2. 先调用 info() 查看基本信息\n3. 根据需求进行数据处理\n4. 将结果赋值给 result 变量，格式为 JSON\n\n## 参考文件\n- references/cheatsheet.md — pandas 常用函数速查表"
}
```

> 关键点：SKILL.md 的完整内容作为 `tool` role 的消息，塞回 messages 列表。LLM 下一轮推理时就能"看到"说明书内容了。

---

### 5.4 第三轮：LLM 读完说明书，决定读参考文件

#### 入参：messages（前一轮基础上追加 tool + ai 消息）

```json
{
  "messages": [
    // 第 1 条: system
    { "role": "system", "content": "你是一个智能助手..." },

    // 第 2 条: 用户问题
    { "role": "human", "content": "用数据分析技能帮我统计一下这个 Excel..." },

    // 第 3 条: LLM 调用 Skill 工具
    {
      "role": "ai",
      "content": "好的，我先查看数据分析技能的使用说明。",
      "tool_calls": [
        { "id": "call_001", "name": "Skill", "args": { "command": "data_analysis" } }
      ]
    },

    // 第 4 条: Skill 工具返回 SKILL.md 内容 ← 上一轮新增
    {
      "role": "tool",
      "tool_call_id": "call_001",
      "content": "# 数据分析技能\n\n## 概述\n..."
    }

    // 注意：这一轮 LLM 请求时，messages 里已经包含了 SKILL.md 的全文
  ],
  "tools": [
    // ... 工具列表不变 ...
  ]
}
```

#### 出参：LLM 返回（决定调用 SkillFile 读取速查表）

```json
{
  "role": "ai",
  "content": "我已了解数据分析技能的基本流程。为了确保使用正确的函数，我先查看一下速查表。",
  "tool_calls": [
    {
      "id": "call_002",
      "name": "SkillFile",
      "args": {
        "skill_name": "data_analysis",
        "path": "references/cheatsheet.md"
      }
    }
  ]
}
```

> LLM 读完 SKILL.md 后，看到里面提到了 `references/cheatsheet.md`，决定用 `SkillFile` 工具读取这个参考文件获取更多细节。

---

### 5.5 第四轮：SkillFile 返回速查表内容

#### 出参：ToolMessage（追加到 messages，作为第 6 条）

```json
{
  "role": "tool",
  "tool_call_id": "call_002",
  "content": "# pandas 速查表\n\n## 读取文件\n- pd.read_excel(path) — 读取Excel\n- pd.read_csv(path) — 读取CSV\n\n## 基本信息\n- df.shape — 行列数\n- df.columns — 列名列表\n- df.dtypes — 每列数据类型\n- df.info() — 完整信息汇总\n\n## 统计描述\n- df.describe() — 数值列统计描述\n- df.value_counts() — 唯一值计数"
}
```

---

### 5.6 第五轮：LLM 读完参考文件，决定执行 Python 代码

#### 入参：messages（已包含 6 条消息）

```json
{
  "messages": [
    // 1: system
    { "role": "system", "content": "你是一个智能助手..." },
    // 2: 用户问题
    { "role": "human", "content": "用数据分析技能帮我统计..." },
    // 3: LLM 调 Skill
    { "role": "ai", "content": "好的，我先查看...", "tool_calls": [{ "id": "call_001", "name": "Skill", ... }] },
    // 4: Skill 返回 SKILL.md
    { "role": "tool", "tool_call_id": "call_001", "content": "# 数据分析技能..." },
    // 5: LLM 调 SkillFile
    { "role": "ai", "content": "我已了解基本流程...", "tool_calls": [{ "id": "call_002", "name": "SkillFile", ... }] },
    // 6: SkillFile 返回速查表 ← 上一轮新增
    { "role": "tool", "tool_call_id": "call_002", "content": "# pandas 速查表..." }
  ],
  "tools": [
    // ... 工具列表不变 ...
  ]
}
```

> 可以看到 messages 越积越长。每一轮对话，历史消息（包括工具调用和结果）都会完整地再发给 LLM。

#### 出参：LLM 返回（决定调用 ExecutePython 执行代码）

```json
{
  "role": "ai",
  "content": "好的，现在我来执行代码读取并统计 Excel 文件的基本信息。",
  "tool_calls": [
    {
      "id": "call_003",
      "name": "ExecutePython",
      "args": {
        "code": "import pandas as pd\nimport json\n\n# 获取文件路径\nfile_path = next(iter(INPUT_FILES.values()))\ndf = pd.read_excel(file_path)\n\n# 统计基本信息\nresult = {\n    \"行数\": df.shape[0],\n    \"列数\": df.shape[1],\n    \"列名\": list(df.columns),\n    \"数据类型\": {col: str(dtype) for col, dtype in df.dtypes.items()}\n}\n\nprint(json.dumps(result, ensure_ascii=False, indent=2))"
      }
    }
  ]
}
```

> LLM 读完 SKILL.md 和速查表后，知道了怎么用 pandas，生成代码调用 `ExecutePython` 工具执行。

---

### 5.7 第六轮：代码执行结果返回 + LLM 生成最终回答

#### ToolMessage（代码执行结果）

```json
{
  "role": "tool",
  "tool_call_id": "call_003",
  "content": "{\n  \"行数\": 1024,\n  \"列数\": 8,\n  \"列名\": [\"订单号\", \"客户名称\", \"金额\", \"日期\", \"状态\", \"地区\", \"销售员\", \"备注\"],\n  \"数据类型\": {\"订单号\": \"object\", \"客户名称\": \"object\", \"金额\": \"int64\", ...}\n}"
}
```

#### 最终 AIMessage（无 tool_calls，结束）

```json
{
  "role": "ai",
  "content": "Excel 文件的基本统计信息如下：\n\n- **行数**：1024 行\n- **列数**：8 列\n- **列名**：订单号、客户名称、金额、日期、状态、地区、销售员、备注\n- **主要数据类型**：金额为整数型，日期为日期型，其余为文本型\n\n需要我进一步做哪些分析吗？比如按地区汇总金额、筛选特定状态的订单等。",
  "tool_calls": []
}
```

> LLM 看到代码执行结果后，组织成自然语言回答用户。没有 tool_calls 表示推理结束，LangGraph 停止循环。

---

### 5.8 完整交互时序图

```
用户                     LangGraph Agent              LLM               Skill 工具         SkillFile 工具      ExecutePython
  │                           │                       │                    │                   │                   │
  │ "用数据分析技能统计Excel"   │                       │                    │                   │                   │
  │──────────────────────────>│                       │                    │                   │                   │
  │                           │  第 1 轮: messages + tools                    │                   │
  │                           │──────────────────────>│                    │                   │
  │                           │                       │                    │                   │
  │                           │  AIMessage            │                    │                   │
  │                           │  content: "我先查看说明"│                    │                   │
  │                           │  tool_calls: [Skill("data_analysis")]       │                   │
  │                           │<──────────────────────│                    │                   │
  │                           │                       │                    │                   │
  │                           │  执行 Skill 工具                              │                   │
  │                           │ read_skill_entrypoint()│                    │                   │
  │                           │──────────────────────────────────────────────>│                   │
  │                           │  SKILL.md 全文        │                    │                   │
  │                           │<──────────────────────────────────────────────│                   │
  │                           │                       │                    │                   │
  │                           │  第 2 轮: messages + ToolMessage(Skill)      │                   │
  │                           │──────────────────────>│                    │                   │
  │                           │                       │                    │                   │
  │                           │  AIMessage            │                    │                   │
  │                           │  content: "我先查看速查表"│                    │                   │
  │                           │  tool_calls: [SkillFile("references/cheatsheet.md")]            │
  │                           │<──────────────────────│                    │                   │
  │                           │                       │                    │                   │
  │                           │  执行 SkillFile 工具                        │                   │
  │                           │ read_skill_file()   │                    │                   │
  │                           │─────────────────────────────────────────────────────────────────>│                   │
  │                           │  速查表内容            │                    │                   │
  │                           │<─────────────────────────────────────────────────────────────────│                   │
  │                           │                       │                    │                   │
  │                           │  第 3 轮: messages + ToolMessage(SkillFile)  │                   │
  │                           │──────────────────────>│                    │                   │
  │                           │                       │                    │                   │
  │                           │  AIMessage            │                    │                   │
  │                           │  content: "现在执行代码"│                    │                   │
  │                           │  tool_calls: [ExecutePython("import pandas...")]                │
  │                           │<──────────────────────│                    │                   │
  │                           │                       │                    │                   │
  │                           │  执行 ExecutePython 工具                                      │
  │                           │───────────────────────────────────────────────────────────────────────────────────────────>│
  │                           │  JSON 结果             │                    │                   │
  │                           │<───────────────────────────────────────────────────────────────────────────────────────────│
  │                           │                       │                    │                   │
  │                           │  第 4 轮: messages + ToolMessage(ExecutePython)                │
  │                           │──────────────────────>│                    │                   │
  │                           │                       │                    │                   │
  │                           │  AIMessage(最终回答)    │                    │                   │
  │                           │  content: "Excel文件共1024行..."            │                   │
  │                           │  tool_calls: []       │                    │                   │
  │                           │<──────────────────────│                    │                   │
  │                           │                       │                    │                   │
  │                           │  无 tool_calls，结束    │                    │                   │
  │ "Excel文件共1024行..."    │                       │                    │                   │
  │<──────────────────────────│                       │                    │                   │
```

### 5.9 messages 增长过程汇总

| 轮次 | messages 条数 | 新增内容 | LLM 动作 |
|------|--------------|----------|---------|
| 第 1 轮 | 2 | system + 用户问题 | 调用 Skill("data_analysis") |
| 第 2 轮 | 4 | + ai(tool_call) + tool(SKILL.md) | 调用 SkillFile("cheatsheet.md") |
| 第 3 轮 | 6 | + ai(tool_call) + tool(速查表) | 调用 ExecutePython(code) |
| 第 4 轮 | 8 | + ai(tool_call) + tool(执行结果) | 生成最终回答，无 tool_calls |

> 每一轮 LLM 请求，messages 列表都会增加 2 条：上一轮的 AIMessage（含 tool_calls）+ ToolMessage（工具返回结果）。这是 ReAct 模式的标准消息格式。

## 六、安全机制

| 安全机制 | 说明 |
|---------|------|
| **🔒 路径越界防护** | SkillFile 工具的 `_resolve_skill_file()` 使用 `resolve()` 规范化路径，确保读取的文件严格在 Skill 目录内，防止 `../../../etc/passwd` 类攻击。 |
| **🌐 URL 安全校验** | `_validate_action_url()` 校验 HTTP action 的 URL，默认禁止内网 IP（127.0.0.1、10.x.x.x、192.168.x.x 等），防止 SSRF 攻击。 |
| **⏱️ 超时限制** | 每个 HTTP Action 超时默认 30 秒，防止慢请求阻塞 Agent 执行。可在 skill.json 中通过 `timeout` 字段自定义。 |
| **✅ 输入 Schema 校验** | 每个 Action 工具的入参由 Pydantic Schema 动态生成，LLM 传入的参数会被自动校验类型和必填项，不符合 Schema 的参数会被拒绝。 |

## 七、核心代码索引

| 文件路径 | 职责 |
|---------|------|
| `backend/core/tools.py` | Skill + SkillFile 两个基础工具的构建逻辑 |
| `backend/core/skill_actions.py` | 从 skill.json 动态构建 HTTP Action 工具 |
| `backend/core/agent_factory.py` | Agent 工厂，统一构建所有工具并创建 LangGraph Agent |
| `backend/services/skill_service.py` | Skill 业务逻辑：CRUD、ZIP 上传、文件读取、清单解析 |
| `backend/services/chat_service.py` | 聊天编排服务，调用 get_agent_skills 加载 Skill 数据 |
| `backend/core/streaming.py` | 流式输出处理，监听 tool_start/tool_end 事件 |
| `backend/core/mcp_tools.py` | MCP 工具构建（与 Skill 工具并行注入） |
| `backend/runtime/tools.py` | Runtime 工具（ExecutePython / RunSkillScript）构建 |
