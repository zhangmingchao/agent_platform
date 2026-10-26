# bi.post.userGroup_notify.6da68355

Airflow 用户分群回调接口 - v1

- 服务：bi；后端相对路径：`/userGroup/notify`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、免登录、服务间调用或维护接口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:195。

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
        "type": "string"
      },
      "version": {
        "type": "string"
      },
      "sql": {
        "type": "string"
      },
      "groupId": {
        "type": "string"
      },
      "dagRunId": {
        "type": "string"
      },
      "errorMsg": {
        "type": "string"
      }
    },
    "x-source-type": "AirFlowCallBackDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/userGroup/AirFlowCallBackDto.java",
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
