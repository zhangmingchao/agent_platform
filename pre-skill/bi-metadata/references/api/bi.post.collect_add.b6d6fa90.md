# bi.post.collect_add.b6d6fa90

增加

- 服务：bi；后端相对路径：`/collect/add`；方法：POST。
- 前端路径：/bi-docker/api/collect/add。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/CollectController.java:31。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:173；方法 collectAdd；参数类型 `CollectType`。

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
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "productKey": {
        "type": "string",
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "type": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "value": {
        "type": "string",
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "createBy": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "createAt": {
        "type": "string",
        "description": "Created by Mybatis Generator 2023/09/21"
      },
      "typeList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "Created by Mybatis Generator 2023/09/21"
      }
    },
    "x-source-type": "HotProfile",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/model/datamanage/HotProfile.java",
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
