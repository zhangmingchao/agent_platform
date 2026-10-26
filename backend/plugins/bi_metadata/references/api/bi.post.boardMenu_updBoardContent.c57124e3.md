# bi.post.boardMenu_updBoardContent.c57124e3

更新看板的内容/(保存)

- 服务：bi；后端相对路径：`/boardMenu/updBoardContent`；方法：POST。
- 前端路径：/bi-docker/api/boardMenu/updBoardContent。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:221。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:10；方法 updateBoard；参数类型 `any`。

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
      "appendData": {
        "type": "boolean"
      },
      "boardReportMapList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "boardId": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "reportFormId": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "createAt": {
              "type": "string",
              "description": "看报-报表中间表 /"
            },
            "createBy": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "layout": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "menuName": {
              "type": "string",
              "description": "看报-报表中间表 /"
            },
            "searchCondition": {
              "type": "string",
              "description": "看报-报表中间表 /"
            }
          },
          "x-source-type": "BoardReportMap",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/model/BoardReportMap.java",
            "line": 1
          }
        }
      }
    },
    "x-source-type": "SaveBoardContentDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/SaveBoardContentDto.java",
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
