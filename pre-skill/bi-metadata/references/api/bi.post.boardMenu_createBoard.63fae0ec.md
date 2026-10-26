# bi.post.boardMenu_createBoard.63fae0ec

创建看板

- 服务：bi；后端相对路径：`/boardMenu/createBoard`；方法：POST。
- 前端路径：/bi-docker/api/boardMenu/createBoard。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:86。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:36；方法 createPanel；参数类型 `TBoard`。

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
        "type": "integer"
      },
      "parentId": {
        "type": "integer"
      },
      "menuName": {
        "type": "string"
      },
      "productKey": {
        "type": "string"
      },
      "authViewType": {
        "type": "integer"
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "roleIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "identity": {
        "type": "integer"
      },
      "tempId": {
        "type": "integer"
      },
      "version": {
        "type": "integer"
      },
      "lastSyncTime": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "boardAction": {
        "x-source-type": "BoardActionEnum",
        "x-source": {
          "project": "bi-docker",
          "file": "da-common/src/main/java/com/reyun/da/common/enums/BoardActionEnum.java",
          "line": 1
        },
        "x-unresolved": "枚举/类型没有可提取字段"
      }
    },
    "x-source-type": "SaveBoardDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/SaveBoardDto.java",
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
