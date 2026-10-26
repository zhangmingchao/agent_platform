# bi.get.profileType_copyEventProfile.06fc77ba

虚拟/汇率属性做关联

- 服务：bi；后端相对路径：`/profileType/copyEventProfile`；方法：GET。
- 前端路径：/bi-docker/api/profileType/copyEventProfile。
- 状态：matched；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:453。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:163；方法 copyProperty；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "profileName": {
        "type": "string"
      },
      "profileClassify": {
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
    }
  ]
}
```
