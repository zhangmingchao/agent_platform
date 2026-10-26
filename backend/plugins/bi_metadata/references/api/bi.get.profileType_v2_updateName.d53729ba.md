# bi.get.profileType_v2_updateName.d53729ba

属性名修改

- 服务：bi；后端相对路径：`/profileType/v2/updateName`；方法：GET。
- 前端路径：/bi-docker/api/profileType/v2/updateName。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:143。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:35；方法 eventEdit；参数类型 `Iedit`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string",
        "description": "产品Key"
      },
      "profileName": {
        "type": "string",
        "description": "属性标识"
      },
      "profileClassify": {
        "type": "integer",
        "description": "属性类型"
      },
      "name": {
        "type": "string",
        "description": "属性名称"
      },
      "id": {
        "type": "number"
      },
      "eventRemark": {
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
