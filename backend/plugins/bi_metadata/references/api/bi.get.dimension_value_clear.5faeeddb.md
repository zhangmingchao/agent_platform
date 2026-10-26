# bi.get.dimension_value_clear.5faeeddb

删除纬度值

- 服务：bi；后端相对路径：`/dimension/value/clear`；方法：GET。
- 前端路径：/bi-docker/api/dimension/value/clear。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/DimensionValueController.java:180。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:339；方法 dimensionClear；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "mainProfile": {
        "type": "string"
      },
      "mainProfileClassify": {
        "type": "integer"
      }
    },
    "required": [
      "mainProfile"
    ],
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
