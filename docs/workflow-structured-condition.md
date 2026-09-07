# 工作流结构化字段条件判断

## 目标

条件节点可以直接读取上一个 Agent 输出的 JSON 字段并选择分支，不再需要使用正则表达式解析 JSON 文本。

## 配置格式

例如，上一个 Agent 输出 `{"type": 1}` 时，可配置：

```json
{
  "label": "类型为 1",
  "type": "structured",
  "field": "type",
  "operator": "eq",
  "value": "1"
}
```

- `field`：点号分隔的字段路径，如 `result.level`、`items.0.name`。
- `operator`：比较操作符。
- `value`：期望值。数字、布尔值和 `null` 按 JSON 类型解析；普通文本按字符串处理。若要匹配字符串 `"1"`，应填写 `"1"`（包含双引号）。

## 支持的操作符

| 操作符 | 含义 | 是否需要期望值 |
| --- | --- | --- |
| `eq` | 类型和值均相等 | 是 |
| `ne` | 类型或值不相等 | 是 |
| `gt` / `gte` | 大于 / 大于等于 | 是 |
| `lt` / `lte` | 小于 / 小于等于 | 是 |
| `contains` | 字符串、数组或对象包含期望值 | 是 |
| `exists` | 字段路径存在，值为 `null` 也算存在 | 否 |
| `not_exists` | 字段路径不存在 | 否 |

## 执行规则

1. 条件按页面中的顺序依次判断，第一条命中的规则生效。
2. 支持纯 JSON 和 Markdown 的 `json` 代码块。
3. JSON 无法解析或字段路径不存在时，该结构化规则不命中。
4. 所有普通规则均未命中时进入 `else` 分支；未配置 `else` 时保持原行为，选择第一个分支。
5. 原有 `contains`、`regex` 和 `else` 配置继续兼容。

## 嵌套字段示例

Agent 输出：

```json
{
  "result": {
    "risk_level": "high"
  }
}
```

条件配置：

```json
{
  "label": "高风险",
  "type": "structured",
  "field": "result.risk_level",
  "operator": "eq",
  "value": "high"
}
```
