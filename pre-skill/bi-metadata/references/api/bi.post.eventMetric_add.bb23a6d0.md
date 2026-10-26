# bi.post.eventMetric_add.bb23a6d0

新增

- 服务：bi；后端相对路径：`/eventMetric/add`；方法：POST。
- 前端路径：/bi-docker/api/eventMetric/add。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventMetricController.java:50。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:169；方法 eventMetric；参数类型 `any`。

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
      "userId": {
        "type": "integer"
      },
      "productKey": {
        "type": "string"
      },
      "category": {
        "type": "integer"
      },
      "metricName": {
        "type": "string"
      },
      "name": {
        "type": "string"
      },
      "remark": {
        "type": "string"
      },
      "metricCondition": {
        "type": "string"
      },
      "status": {
        "type": "integer"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "updateAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "removeStatus": {
        "type": "integer"
      },
      "searchText": {
        "type": "string"
      },
      "sortFieldName": {
        "type": "string"
      },
      "sortType": {
        "type": "integer"
      },
      "isGetAll": {
        "type": "boolean",
        "description": "是否查询所有可见指标 /"
      },
      "isCollect": {
        "type": "integer",
        "description": "是否收藏 /"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "是否收藏 /"
      },
      "currentTimeZoneOffset": {
        "type": "string",
        "description": "是否收藏 /"
      }
    },
    "x-source-type": "EventMetricDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventMetricDto.java",
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
