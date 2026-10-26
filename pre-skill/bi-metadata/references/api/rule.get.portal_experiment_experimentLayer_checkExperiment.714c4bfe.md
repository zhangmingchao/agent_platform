# rule.get.portal_experiment_experimentLayer_checkExperiment.714c4bfe

CheckExperimentLayerCanDelete 检查试验层关联的试验

- 服务：rule；后端相对路径：`/portal/experiment/experimentLayer/checkExperiment`；方法：GET。
- 前端路径：/portal/ab/experiment/experimentLayer/checkExperiment。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:174。
- 后端源码：rule/router/experiment/experiment_layer.go:170。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:120；方法 experimentLayerDeleteCheckExperiment；参数类型 `TestBedId`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "number",
        "description": "试验层主键Id"
      }
    },
    "required": [
      "id"
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
  "backend_type": "e.Response {code,msg,data,trace,timeZone}",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer"
      },
      "msg": {
        "type": "string"
      },
      "data": {},
      "trace": {
        "type": "string"
      },
      "timeZone": {
        "type": "string"
      }
    }
  },
  "frontend_schemas": [
    {
      "type": "boolean"
    }
  ]
}
```
