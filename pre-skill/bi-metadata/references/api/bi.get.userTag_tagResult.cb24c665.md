# bi.get.userTag_tagResult.cb24c665

标签值分布

- 服务：bi；后端相对路径：`/userTag/tagResult`；方法：GET。
- 前端路径：/bi-docker/api/userTag/tagResult。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:134。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:38；方法 getTagResult；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "标签ID"
      }
    },
    "required": [
      "id"
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
  "backend_type": "ResultModel<List<UserTagResultDto>>",
  "backend_schema": {
    "x-source-type": "ResultModel<List<UserTagResultDto>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
