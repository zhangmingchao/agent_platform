# bi.get.userTag_delVerify.14cb93e0

获取标签用户的属性列表

- 服务：bi；后端相对路径：`/userTag/delVerify`；方法：GET。
- 前端路径：/bi-docker/api/userTag/delVerify。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:264。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:30；方法 delGroupVerify；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
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
  "backend_type": "ResultModel<Map<String, Object>>",
  "backend_schema": {
    "x-source-type": "ResultModel<Map<String, Object>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
