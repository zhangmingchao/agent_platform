# rule.post.config_openEngineLog.523f1102

OpenEngineLog 打开引擎错误日志

- 服务：rule；后端相对路径：`/config/openEngineLog`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：内部 SDK、回调或运维接口，无 Portal 业务代理
- 后端源码：rule/router/portal.go:143。
- 后端源码：rule/router/config/config.go:153。

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
      "token": {
        "type": "string"
      },
      "log_status": {
        "type": "integer"
      }
    },
    "x-source-type": "dto.OpenEngineLogDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/config.go",
      "line": 1
    }
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
