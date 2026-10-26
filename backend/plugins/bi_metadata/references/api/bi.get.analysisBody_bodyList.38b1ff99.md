# bi.get.analysisBody_bodyList.38b1ff99

产品的主体列表

- 服务：bi；后端相对路径：`/analysisBody/bodyList`；方法：GET。
- 前端路径：/bi-docker/api/analysisBody/bodyList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/AnalysisBodyController.java:46。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:137；方法 getSubjectList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      }
    },
    "required": [
      "productKey"
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
  "backend_type": "ResultModel<List<AnalysisBodyVo>>",
  "backend_schema": {
    "x-source-type": "ResultModel<List<AnalysisBodyVo>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
