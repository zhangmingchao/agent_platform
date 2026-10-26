# bi.post.groupTemplate_verifyBatch.04f6675f

模板创建看板-批量校验接口

- 服务：bi；后端相对路径：`/groupTemplate/verifyBatch`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/verifyBatch。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:134。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:76；方法 verifyBatchTemplate；参数类型 `any`。

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
      "productIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "boardTempIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "roleIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "authViewType": {
        "type": "integer",
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "parentId": {
        "type": "integer",
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      }
    },
    "x-source-type": "GroupTempReqBatchDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempReqBatchDto.java",
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
