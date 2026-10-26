# bi.post.groupTemplate_editInfo.c5f9b8e7

编辑模板

- 服务：bi；后端相对路径：`/groupTemplate/editInfo`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/editInfo。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:79。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:24；方法 editTemplate；参数类型 `any`。

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
      "id": {
        "type": "integer"
      },
      "boardId": {
        "type": "integer"
      },
      "name": {
        "type": "string"
      },
      "desc": {
        "type": "string"
      },
      "loginUserId": {
        "type": "integer"
      },
      "tenantId": {
        "type": "integer"
      }
    },
    "x-source-type": "GroupTemplateInfoVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/grouptemplate/GroupTemplateInfoVo.java",
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
