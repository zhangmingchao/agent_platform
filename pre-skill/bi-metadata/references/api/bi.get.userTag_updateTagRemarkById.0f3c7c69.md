# bi.get.userTag_updateTagRemarkById.0f3c7c69

修改用户标签名称

- 服务：bi；后端相对路径：`/userTag/updateTagRemarkById`；方法：GET。
- 前端路径：/bi-docker/api/userTag/updateTagRemarkById。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:69。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:22；方法 updateTagRemarkById；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "remark": {
        "type": "string"
      }
    },
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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
