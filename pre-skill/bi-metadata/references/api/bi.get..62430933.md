# bi.get..62430933

apiIndex

- 服务：bi；后端相对路径：`/`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、维护、认证或服务间调用 Controller，非 Agent 业务入口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/ApiDoController.java:35。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
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
  "backend_type": "String",
  "backend_schema": {
    "type": "string"
  },
  "frontend_schemas": []
}
```
