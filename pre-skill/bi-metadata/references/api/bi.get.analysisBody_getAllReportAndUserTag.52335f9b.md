# bi.get.analysisBody_getAllReportAndUserTag.52335f9b

根据主体ID获取关联报表和标签

- 服务：bi；后端相对路径：`/analysisBody/getAllReportAndUserTag`；方法：GET。
- 前端路径：/bi-docker/api/analysisBody/getAllReportAndUserTag。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/AnalysisBodyController.java:108。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:157；方法 getAllReportAndUserGroup；参数类型 `any`。

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
  "backend_type": "ResultModel<AnalysisBodyReferenceVO>",
  "backend_schema": {
    "x-source-type": "ResultModel<AnalysisBodyReferenceVO>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
