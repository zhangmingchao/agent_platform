# bi.get.timeZone_getCurrentTimeZoneDetail.58f8e802

获取时区对应的小时小时

- 服务：bi；后端相对路径：`/timeZone/getCurrentTimeZoneDetail`；方法：GET。
- 前端路径：/bi-docker/api/timeZone/getCurrentTimeZoneDetail。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/util/TimeZoneController.java:62。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:70；方法 getTimeZoneHours；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
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
