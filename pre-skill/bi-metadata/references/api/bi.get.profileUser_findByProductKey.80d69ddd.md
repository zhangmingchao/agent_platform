# bi.get.profileUser_findByProductKey.80d69ddd

用户属性列表(废弃)

- 服务：bi；后端相对路径：`/profileUser/findByProductKey`；方法：GET。
- 前端路径：/bi-docker/api/profileUser/findByProductKey。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:150。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:82；方法 userList；参数类型 `selectType`。

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
      "pageNum": {
        "type": "integer",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "default": 50,
        "maximum": 200
      },
      "searchText": {
        "type": "string",
        "description": "搜索内容"
      },
      "eventName": {
        "type": "string"
      },
      "profileClassifyList": {
        "type": "array",
        "items": {
          "type": "number"
        }
      },
      "profileTypeList": {
        "type": "array",
        "items": {
          "type": "string"
        }
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
