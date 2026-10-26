# bi.post.dimension_value_delete.17a47eca

删除维度值

- 服务：bi；后端相对路径：`/dimension/value/delete`；方法：POST。
- 前端路径：/bi-docker/api/dimension/value/delete。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/DimensionValueController.java:165。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:351；方法 dimensionDelete；参数类型 `any`。

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
      "tenantId": {
        "type": "string"
      },
      "prokey": {
        "type": "string"
      },
      "uploadType": {
        "type": "integer"
      },
      "dimensionName": {
        "type": "string"
      },
      "dimensionKey": {
        "type": "string"
      },
      "dimensionVal": {
        "type": "string"
      },
      "createBy": {
        "type": "integer"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "updateBy": {
        "type": "integer"
      },
      "updateAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "mainProfile": {
        "type": "string"
      }
    },
    "x-source-type": "DimensionValueVO",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/DimensionValueVO.java",
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
