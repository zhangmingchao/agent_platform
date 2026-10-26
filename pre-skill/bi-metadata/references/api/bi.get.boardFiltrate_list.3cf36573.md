# bi.get.boardFiltrate_list.3cf36573

list

- 服务：bi；后端相对路径：`/boardFiltrate/list`；方法：GET。
- 前端路径：/bi-docker/api/boardFiltrate/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardFiltrateCollectController.java:30。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:59；方法 fetchGlobalFiltrateList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "boardId": {
        "type": "integer"
      }
    },
    "additionalProperties": false
  },
  "body_schema": null,
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
