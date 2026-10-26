# bi.get.boardMenu_createFolder.164ed95a

创建文件夹

- 服务：bi；后端相对路径：`/boardMenu/createFolder`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/createFolder。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:64。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:32；方法 createFolder；参数类型 `TFolder`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "folderName": {
        "type": "string"
      },
      "productKey": {
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
  "backend_type": "ResultModel<BoardMenu>",
  "backend_schema": {
    "x-source-type": "ResultModel<BoardMenu>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
