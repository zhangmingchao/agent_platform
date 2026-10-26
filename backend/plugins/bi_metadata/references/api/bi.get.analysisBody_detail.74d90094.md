# bi.get.analysisBody_detail.74d90094

详情

- 服务：bi；后端相对路径：`/analysisBody/detail`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/AnalysisBodyController.java:87。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "bodyId": {
        "type": "integer"
      }
    },
    "required": [
      "bodyId"
    ],
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
  "backend_type": "ResultModel<AnalysisBodyVo>",
  "backend_schema": {
    "x-source-type": "ResultModel<AnalysisBodyVo>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
