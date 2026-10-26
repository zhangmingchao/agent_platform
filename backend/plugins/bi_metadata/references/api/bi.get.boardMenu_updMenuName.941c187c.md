# bi.get.boardMenu_updMenuName.941c187c

修改文件夹/看板名称

- 服务：bi；后端相对路径：`/boardMenu/updMenuName`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/updMenuName。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:75。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:44；方法 updateFolderName；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "newMenuName": {
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
  "backend_type": "ResultModel<Boolean>",
  "backend_schema": {
    "x-source-type": "ResultModel<Boolean>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
