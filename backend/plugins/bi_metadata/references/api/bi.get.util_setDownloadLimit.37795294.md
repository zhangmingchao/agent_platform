# bi.get.util_setDownloadLimit.37795294

setAnalysisLimit

- 服务：bi；后端相对路径：`/util/setDownloadLimit`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/util/UtilController.java:78。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer"
      }
    },
    "additionalProperties": false
  },
  "body_schema": null,
  "path_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

返回声明：

```json
{
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
