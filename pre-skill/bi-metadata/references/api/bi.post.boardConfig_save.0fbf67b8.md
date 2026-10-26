# bi.post.boardConfig_save.0fbf67b8

#endregion 看板设置

- 服务：bi；后端相对路径：`/boardConfig/save`；方法：POST。
- 前端路径：/bi-docker/api/boardConfig/save。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardSettingController.java:37。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:71；方法 boardSetting；参数类型 `any`。

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
      "id": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2024/08/07 /"
      },
      "boardId": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2024/08/07 /"
      },
      "isApproximate": {
        "type": "boolean",
        "description": "Created by Mybatis Generator 2024/08/07 /"
      },
      "reportTime": {
        "type": "string",
        "description": "Created by Mybatis Generator 2024/08/07 /"
      },
      "fixedTimeCompute": {
        "type": "string",
        "description": "看板统一时间 /"
      },
      "timeZone": {
        "type": "string",
        "description": "看板统一时区 /"
      },
      "lastComputeTime": {
        "type": "string",
        "description": "看板统一时区 /"
      },
      "createAt": {
        "type": "string",
        "description": "看板统一时区 /"
      },
      "updateAt": {
        "type": "string",
        "description": "看板统一时区 /"
      },
      "status": {
        "type": "integer",
        "description": "看板统一时区 /"
      },
      "createBy": {
        "type": "integer",
        "description": "看板统一时区 /"
      },
      "updateBy": {
        "type": "integer",
        "description": "看板统一时区 /"
      },
      "boardFiltrate": {
        "type": "string",
        "description": "看板统一时区 /"
      },
      "computeTimeZone": {
        "type": "string",
        "description": "看板统一时区 /"
      }
    },
    "x-source-type": "BoardSetting",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/model/BoardSetting.java",
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
