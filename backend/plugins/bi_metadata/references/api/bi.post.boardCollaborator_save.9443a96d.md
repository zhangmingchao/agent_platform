# bi.post.boardCollaborator_save.9443a96d

保存协作者

- 服务：bi；后端相对路径：`/boardCollaborator/save`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardCollaboratorController.java:32。

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
      "boardId": {
        "type": "integer"
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      }
    },
    "x-source-type": "BoardCollaboratorDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/BoardCollaboratorDto.java",
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
  "backend_type": "ResultModel<Boolean>",
  "backend_schema": {
    "x-source-type": "ResultModel<Boolean>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
