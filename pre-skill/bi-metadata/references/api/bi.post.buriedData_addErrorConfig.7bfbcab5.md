# bi.post.buriedData_addErrorConfig.7bfbcab5

新增错误配置

- 服务：bi；后端相对路径：`/buriedData/addErrorConfig`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/BuriedDataController.java:163。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "false": {
        "type": "boolean",
        "default": false
      }
    },
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "productKey": {
        "type": "string"
      },
      "moduleType": {
        "type": "integer"
      },
      "errType": {
        "type": "integer"
      },
      "profileName": {
        "type": "string"
      },
      "tableType": {
        "type": "integer"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "createBy": {
        "type": "integer"
      },
      "desc": {
        "type": "string"
      }
    },
    "x-source-type": "ErrorConfigDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/buried/ErrorConfigDto.java",
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
