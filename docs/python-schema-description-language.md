# Python Schema 描述语言

## 目标

Agent 创建页支持使用 Pydantic 风格语法描述结构化输出。该文本只是 Schema 描述语言，
服务器不会执行它。保存时，后端使用 Python `ast` 模块读取声明并转换成标准 JSON Schema；
数据库仍保存 JSON Schema，大模型最终仍输出 JSON。

```text
Python 风格描述 -> AST 白名单解析 -> JSON Schema -> 模型约束 -> JSON 输出 -> JSON Schema 校验
```

## 示例

```python
class PersonInfo(BaseModel):
    name: str = Field(description="人物的姓名")
    age: int = Field(ge=0, le=150, description="人物的年龄")
    hobby: Optional[str] = Field(default=None, description="人物的爱好")
    tags: list[str] = Field(default_factory=list)
```

支持的基础类型：`str`、`int`、`float`、`bool`、`Any`。

支持的容器类型：`list/List`、`dict/Dict`、`Optional`、`Literal`，并支持引用同一描述中的
嵌套 `BaseModel` 类。多个类存在时，最后一个类作为根输出模型。

支持的 `Field` 参数：`description`、`title`、`default`、`default_factory`、`ge`、`gt`、
`le`、`lt`、`min_length`、`max_length`、`pattern`。`default_factory` 仅支持 `list` 和 `dict`。

## 安全边界

转换器位于 `backend/core/schema_dsl.py`，只使用 `ast.parse` 和 `ast.literal_eval`，禁止：

- `exec`、`eval` 以及任何代码执行；
- 顶层表达式和函数调用；
- 类方法、装饰器及任意继承；
- 任意属性访问和任意函数调用；
- 非白名单导入；
- 超过 20000 字符的描述。

为了方便粘贴现有示例，可以出现受限的 `pydantic` 与 `typing` 导入，但这些导入只会被
AST 校验，不会实际运行。其他导入全部拒绝。常见的 `Field(..., description="必填")` 也会
被识别为必填字段。

## API

- `POST /api/output-schema/python-to-json`：接收 `{"source": "..."}`，返回 `{"schema": {...}}`。
- `POST /api/output-schema/json-to-python`：接收 `{"schema_data": {...}}`，返回规范化描述文本。

两个接口都要求登录。Agent 保存接口仍只接收标准 `output_schema`，因此聊天、工作流、SSE
和历史 Agent 数据不需要迁移。

## 前端行为

创建 Agent 时默认显示“Python 模型”模式，也可以切换到“JSON Schema”。切换时调用后端
转换接口，两种模式始终操作同一份 Schema。编辑历史 Agent 时，前端会把数据库中的 JSON
Schema 转成 Python 描述；遇到暂不支持反向表示的复杂 Schema，则自动保留 JSON 模式。
