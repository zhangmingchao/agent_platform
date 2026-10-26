# bi.get.report_userDetail.c01360b7

用户详情-明细

- 服务：bi；后端相对路径：`/report/userDetail`；方法：GET。
- 前端路径：/bi-docker/api/report/userDetail。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BehaviorAnalysisReportController.java:823。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:225；方法 userDetail；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "userId": {
        "type": "string",
        "description": "@Author zc @Description 用户 @Date 2021/9/14 15:18 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description 用户 @Date 2021/9/14 15:18 /"
      },
      "userPropertiesList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "用户属性列表 /"
      },
      "entityType": {
        "type": "string",
        "description": "用户属性列表 /"
      },
      "tableType": {
        "type": "string",
        "description": "用户属性列表 /"
      },
      "timeZone": {
        "type": "string",
        "description": "用户属性列表 /"
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
    }
  ]
}
```
