# bi.post.buriedData_buriedDataListV.fb3c536e

埋点数据列表查询V

- 服务：bi；后端相对路径：`/buriedData/buriedDataListV`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/BuriedDataController.java:114。

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
      "productKey": {
        "type": "string"
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "startDate": {
        "type": "string"
      },
      "endDate": {
        "type": "string"
      },
      "pageNum": {
        "type": "integer"
      },
      "pageSize": {
        "type": "integer"
      },
      "eventTitle": {
        "type": "string"
      },
      "errType": {
        "type": "integer"
      },
      "errTitle": {
        "type": "integer"
      },
      "ignoreCodeList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "titleList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "offsetPre": {
        "type": "integer"
      },
      "offsetAft": {
        "type": "integer"
      },
      "timeZone": {
        "type": "string"
      },
      "dt": {
        "type": "string"
      },
      "blackList": {
        "type": "string"
      },
      "failCode": {
        "type": "string"
      },
      "otherCode": {
        "type": "string"
      },
      "errCode": {
        "type": "string"
      },
      "sortFieldName": {
        "type": "string"
      },
      "sortType": {
        "type": "integer"
      },
      "moduleType": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "tableType": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "inDbTable": {
        "type": "string",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "errorTable": {
        "type": "string",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "total": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "isAllApp": {
        "type": "boolean",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "eventClassify": {
        "type": "integer",
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      },
      "blackEventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "3, \"分析\" 1,”系统\" 4, \"归因\" 必穿 /"
      }
    },
    "x-source-type": "BuriedDataDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/buried/BuriedDataDto.java",
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
  "backend_type": "ResultModel<ErrorDataListVo>",
  "backend_schema": {
    "x-source-type": "ResultModel<ErrorDataListVo>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
