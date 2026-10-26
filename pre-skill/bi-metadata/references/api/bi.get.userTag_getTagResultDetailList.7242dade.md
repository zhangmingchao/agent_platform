# bi.get.userTag_getTagResultDetailList.7242dade

查询标签值分布

- 服务：bi；后端相对路径：`/userTag/getTagResultDetailList`；方法：GET。
- 前端路径：/bi-docker/api/userTag/getTagResultDetailList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:141。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:34；方法 getTagResultDetailList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "标签ID"
      },
      "pageNum": {
        "type": "integer",
        "default": 1,
        "minimum": 1
      },
      "pageSize": {
        "type": "integer",
        "default": 50,
        "minimum": 1,
        "maximum": 200
      }
    },
    "required": [
      "id"
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
