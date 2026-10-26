# bi.get.boardMenu_templateBoardList.ace6d644

模板下看板列表

- 服务：bi；后端相对路径：`/boardMenu/templateBoardList`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/templateBoardList。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:144。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:20；方法 fetchBoardList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "boardName": {
        "type": "string"
      },
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
  "backend_type": "ResultModel<PageResultModel<BoardMenuVo>>",
  "backend_schema": {
    "x-source-type": "ResultModel<PageResultModel<BoardMenuVo>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
