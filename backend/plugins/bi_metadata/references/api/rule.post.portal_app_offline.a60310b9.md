# rule.post.portal_app_offline.a60310b9

app.Offline

- 服务：rule；后端相对路径：`/portal/app/offline`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：内部 SDK、回调或运维接口，无 Portal 业务代理
- 后端源码：rule/router/portal.go:232。
- 后端源码：rule/router/app/app.go:16。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "app_ids": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      }
    },
    "x-source-type": "OfflineRequest",
    "x-source": {
      "project": "rule",
      "file": "router/app/app.go",
      "line": 1
    },
    "required": [
      "app_ids"
    ]
  },
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
  "frontend_schemas": []
}
```
