# bi.get.userTag_transConditionTag.f88a422c

回调分群执行

- 服务：bi；后端相对路径：`/userTag/transConditionTag`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:321。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "userId": {
        "type": "integer"
      },
      "tagId": {
        "type": "integer"
      }
    },
    "required": [
      "userId"
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
  "backend_type": "ResultModel<String>",
  "backend_schema": {
    "x-source-type": "ResultModel<String>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
