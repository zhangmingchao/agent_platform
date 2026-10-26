# bi.post.report_findProfVal.74b90b75

属性数值下拉

- 服务：bi；后端相对路径：`/report/findProfVal`；方法：POST。
- 前端路径：/bi-docker/api/report/findProfVal。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BehaviorAnalysisReportController.java:771。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:97；方法 getPofileValues；参数类型 `any`。

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
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "profileName": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "type": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "timeType": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      },
      "profileClassify": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/6/1 16:50 /"
      }
    },
    "x-source-type": "ProfileValVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/ProfileValVo.java",
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
