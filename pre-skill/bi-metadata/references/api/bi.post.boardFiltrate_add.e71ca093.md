# bi.post.boardFiltrate_add.e71ca093

列表

- 服务：bi；后端相对路径：`/boardFiltrate/add`；方法：POST。
- 前端路径：/bi-docker/api/boardFiltrate/add。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardFiltrateCollectController.java:38。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:50；方法 storeGlobalFiltrate；参数类型 `any`。

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
      "productKey": {
        "type": "string"
      },
      "boardId": {
        "type": "integer"
      },
      "name": {
        "type": "string"
      },
      "filtrate": {
        "type": "string"
      },
      "isDefault": {
        "type": "integer"
      },
      "isDel": {
        "type": "boolean"
      },
      "createBy": {
        "type": "integer"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "updateBy": {
        "type": "integer"
      },
      "updateAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "boardIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      }
    },
    "x-source-type": "BoardFiltrateCollect",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/model/BoardFiltrateCollect.java",
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
