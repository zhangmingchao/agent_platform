# bi.post.userTag_notify.9735484b

Airflow用户标签回调接口

- 服务：bi；后端相对路径：`/userTag/notify`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、免登录、服务间调用或维护接口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:283。

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
      "state": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "version": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "sql": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "tagId": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "dagRunId": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "errorMsg": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      },
      "tagResultList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "tagResultId": {
              "type": "string"
            },
            "state": {
              "type": "string"
            }
          },
          "x-source-type": "AirFlowCallbackTagResultDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/dto/userGroup/AirFlowCallbackTagResultDto.java",
            "line": 1
          }
        },
        "description": "@Author zc @Description TODO @Date 2023/8/23 12:04 /"
      }
    },
    "x-source-type": "AirFlowCallbackTagDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/userGroup/AirFlowCallbackTagDto.java",
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
