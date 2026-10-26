# bi.get.reportForm_getReportInfoById.b5c7459c

报表详情

- 服务：bi；后端相对路径：`/reportForm/getReportInfoById`；方法：GET。
- 前端路径：/bi-docker/api/reportForm/getReportInfoById。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/ReportFormMenuController.java:142。
- 前端源码：solar-engine-fe/src/api/modules/anasysis/index.ts:55；方法 getDetail；参数类型 `any`。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:90；方法 getReportDetail；参数类型 `TDetail`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "boardId": {
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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    },
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
