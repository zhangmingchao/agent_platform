# bi.post.noLogin_audience_createAudienceBaseInfo.b92945af

createAudienceBaseInfo

- 服务：bi；后端相对路径：`/noLogin/audience/createAudienceBaseInfo`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、维护、认证或服务间调用 Controller，非 Agent 业务入口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/NoLoginCdpAudienceConfigController.java:31。

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
      "appKey": {
        "type": "string"
      },
      "tagId": {
        "type": "string",
        "description": ""
      },
      "tagName": {
        "type": "string",
        "description": ""
      },
      "remark": {
        "type": "string",
        "description": ""
      },
      "tagValueType": {
        "type": "integer",
        "description": ""
      },
      "updateType": {
        "type": "integer",
        "description": ""
      },
      "tagValue": {
        "type": "string",
        "description": ""
      },
      "entityType": {
        "type": "string",
        "description": ""
      },
      "audienceModule": {
        "type": "integer",
        "description": ""
      },
      "userId": {
        "type": "integer",
        "description": ""
      }
    },
    "x-source-type": "OpenApiUserGroupDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/userGroup/OpenApiUserGroupDto.java",
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
  "frontend_schemas": []
}
```
