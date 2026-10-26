# rule.get.portal_params_verifyParamName.2468a04b

VerifyParamName 验证参数名称

- 服务：rule；后端相对路径：`/portal/params/verifyParamName`；方法：GET。
- 前端路径：/portal/rule/params/verifyParamName。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:211。
- 后端源码：rule/router/param_info.go:84。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:31；方法 verifyParamName；参数类型 `VerifyParamName`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "appId": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "string",
            "const": ""
          }
        ]
      },
      "paramName": {
        "type": "string",
        "description": "参数名称"
      }
    },
    "required": [
      "appId",
      "paramName"
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
