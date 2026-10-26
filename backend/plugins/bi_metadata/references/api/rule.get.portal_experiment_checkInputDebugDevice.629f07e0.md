# rule.get.portal_experiment_checkInputDebugDevice.629f07e0

校验调试设备

- 服务：rule；后端相对路径：`/portal/experiment/checkInputDebugDevice`；方法：GET。
- 前端路径：/portal/ab/experiment/checkInputDebugDevice。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:155。
- 后端源码：rule/router/experiment/experiment.go:308。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:83；方法 checkDebugDevice；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "appId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "deviceId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "experimentLayerId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "experimentId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "appId",
      "deviceId",
      "experimentLayerId"
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
