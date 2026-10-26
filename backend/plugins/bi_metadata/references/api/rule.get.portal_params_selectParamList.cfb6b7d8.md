# rule.get.portal_params_selectParamList.cfb6b7d8

GetSelectParamList 获取参数下拉列表

- 服务：rule；后端相对路径：`/portal/params/selectParamList`；方法：GET。
- 前端路径：/portal/rule/params/selectParamList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:215。
- 后端源码：rule/router/param_info.go:194。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:61；方法 selectParamList；参数类型 `SelectParamList`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "appId": {
        "type": "number"
      },
      "text": {
        "type": "string"
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
