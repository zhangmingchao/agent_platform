# rule.get.portal_experiment_list.09374427

List 试验列表

- 服务：rule；后端相对路径：`/portal/experiment/list`；方法：GET。
- 前端路径：/portal/ab/experiment/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:153。
- 后端源码：rule/router/experiment/experiment.go:152。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:12；方法 testList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "pageNum": {
        "type": "integer",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "default": 50,
        "maximum": 200
      },
      "orderBy": {
        "type": "string"
      },
      "orderColumn": {
        "type": "string"
      },
      "status": {
        "type": "integer"
      },
      "experimentLayerId": {
        "type": "integer"
      },
      "name": {
        "type": "string"
      },
      "appId": {
        "type": "integer"
      }
    },
    "required": [
      "appId"
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
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
