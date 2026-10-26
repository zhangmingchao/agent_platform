# bi.get.groupTemplate_listPage.cc808649

获取模板列表 分页查询

- 服务：bi；后端相对路径：`/groupTemplate/listPage`；方法：GET。
- 前端路径：/bi-docker/api/groupTemplate/listPage。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:56。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:16；方法 fetchTemplateList；参数类型 `TFetchTemplateListParam`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "0": {
        "type": "integer",
        "default": 0
      },
      "10": {
        "type": "integer",
        "default": 10
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
  "backend_type": "ResultModel<PageResultModel<GroupTemplateInfoDto>>",
  "backend_schema": {
    "x-source-type": "ResultModel<PageResultModel<GroupTemplateInfoDto>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
