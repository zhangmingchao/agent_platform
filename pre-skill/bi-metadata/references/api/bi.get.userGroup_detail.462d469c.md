# bi.get.userGroup_detail.462d469c

分群列表

- 服务：bi；后端相对路径：`/userGroup/detail`；方法：GET。
- 前端路径：/bi-docker/api/userGroup/detail。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:64。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:49；方法 getGroupDetail；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "groupId": {
        "type": "integer",
        "description": "分群ID"
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
  "backend_type": "ResultModel<UserGroup>",
  "backend_schema": {
    "x-source-type": "ResultModel<UserGroup>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
