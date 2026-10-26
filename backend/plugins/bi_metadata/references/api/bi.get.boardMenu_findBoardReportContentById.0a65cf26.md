# bi.get.boardMenu_findBoardReportContentById.0a65cf26

获取看板的内容

- 服务：bi；后端相对路径：`/boardMenu/findBoardReportContentById`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/findBoardReportContentById。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:205。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:7；方法 getBoardDetail；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "看板ID"
      },
      "responseSimple": {
        "type": "boolean",
        "description": "简单返回",
        "default": false
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
