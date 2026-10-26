# bi.post.buriedData_getEventStartPerm.c15178a7

设置启用禁用状态V

- 服务：bi；后端相对路径：`/buriedData/getEventStartPerm`；方法：POST。
- 前端路径：/bi-docker/api/buriedData/getEventStartPerm。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/BuriedDataController.java:80。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:183；方法 getEventStartPerm；参数类型 `any`。

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
      "productKey": {
        "type": "string",
        "description": "选择了哪些app /"
      },
      "eventName": {
        "type": "string",
        "description": "事件名称 /"
      },
      "appkeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "状态类型 1全部开启.2全部关闭.3部分开启 /"
      },
      "appIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "状态类型 1全部开启.2全部关闭.3部分开启 /"
      },
      "statusType": {
        "type": "integer",
        "description": "状态类型 1全部开启.2全部关闭.3部分开启 /"
      },
      "moduleType": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" /"
      },
      "isAllApp": {
        "type": "boolean",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" /"
      },
      "status": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" /"
      },
      "eventClassify": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" /"
      }
    },
    "x-source-type": "BuriedDataStatusDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/buried/BuriedDataStatusDto.java",
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
