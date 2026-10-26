# bi.post.profileRecort_saveRecord.f93c464d

保存记录

- 服务：bi；后端相对路径：`/profileRecort/saveRecord`；方法：POST。
- 前端路径：/bi-docker/api/profileRecort/saveRecord。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/analysis/SelectProfileRecordController.java:28。
- 前端源码：solar-engine-fe/src/api/modules/anasysisReport/index.ts:95；方法 saveProperty；参数类型 `any`。

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
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "productKey": {
        "type": "string",
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "createBy": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "value": {
        "type": "string",
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "tableName": {
        "type": "string",
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "createAt": {
        "type": "string",
        "description": "Created by Mybatis Generator 2024/01/09 /"
      },
      "saveVal": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "entityType": {
        "type": "string"
      },
      "pageKey": {
        "type": "string"
      }
    },
    "x-source-type": "SelectProfileRecordVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/analysis/SelectProfileRecordVo.java",
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
