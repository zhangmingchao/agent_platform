# rule.get.portal_experiment_urlVerify.2e1ce4a6

UrlVerify 试验url校验

- 服务：rule；后端相对路径：`/portal/experiment/urlVerify`；方法：GET。
- 前端路径：/portal/ab/experiment/urlVerify。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:157。
- 后端源码：rule/router/experiment/experiment.go:360。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:134；方法 experimentUrlVerify；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "experimentUrl": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "experimentLayerId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "matchType": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "experimentLayerId",
      "experimentUrl",
      "matchType"
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
