# bi.post.groupTemplateRelation_list.f711ee1b

模板关联看板列表

- 服务：bi；后端相对路径：`/groupTemplateRelation/list`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplateRelation/list。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateRelationController.java:30。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:44；方法 fetchRelatedBoard；参数类型 `any`。

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
    "additionalProperties": {
      "x-source-type": "Object",
      "x-unresolved": "动态 JSON，参数形状需查调用页面"
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
  "backend_type": "ResultModel<PageResultModel<GroupTemplateBoardRelationDto>>",
  "backend_schema": {
    "x-source-type": "ResultModel<PageResultModel<GroupTemplateBoardRelationDto>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
