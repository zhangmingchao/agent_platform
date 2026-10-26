# bi.post.boardMenu_copyBoard.fef70be8

复制接口

- 服务：bi；后端相对路径：`/boardMenu/copyBoard`；方法：POST。
- 前端路径：/bi-docker/api/boardMenu/copyBoard。
- 状态：matched；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:158。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:56；方法 clonePanelInfo；参数类型 `any`。

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
      }
    },
    "x-source-type": "CopyBoardDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/CopyBoardDto.java",
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
