# bi.get.report_checkAnalysisBody.18696097

检查分析主体与当前应用是否匹配

- 服务：bi；后端相对路径：`/report/checkAnalysisBody`；方法：GET。
- 前端路径：/bi-docker/api/report/checkAnalysisBody。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BehaviorAnalysisReportController.java:837。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:165；方法 checkAnalysisBody；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "analysisBodyId": {
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
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
