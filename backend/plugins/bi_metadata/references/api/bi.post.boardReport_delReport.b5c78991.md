# bi.post.boardReport_delReport.b5c78991

删除看板中的报表

- 服务：bi；后端相对路径：`/boardReport/delReport`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardReportMapController.java:40。

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
  "frontend_schemas": []
}
```
