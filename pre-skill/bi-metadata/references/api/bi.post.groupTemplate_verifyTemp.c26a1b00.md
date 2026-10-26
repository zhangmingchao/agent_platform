# bi.post.groupTemplate_verifyTemp.c26a1b00

模板创建看板-校验接口

- 服务：bi；后端相对路径：`/groupTemplate/verifyTemp`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/verifyTemp。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:152。
- 前端源码：solar-engine-fe/src/api/modules/template/index.ts:26；方法 postVerifyTemp；参数类型 `any`。

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
      "productId": {
        "type": "integer",
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "boardTempId": {
        "type": "integer",
        "description": "@Author zc @Description 集团模板-创建看板校验 @Date 2023/6/14 10:59 /"
      },
      "menuName": {
        "type": "string",
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
    "x-source-type": "GroupTempReqDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempReqDto.java",
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
  "backend_type": "ResultModel",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msg": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "timeZone": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "data": {
        "x-source-type": "T",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msgType": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      }
    },
    "x-source-type": "ResultModel",
    "x-source": {
      "project": "bi-docker",
      "file": "da-common/src/main/java/com/reyun/da/common/api/ResultModel.java",
      "line": 1
    }
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
