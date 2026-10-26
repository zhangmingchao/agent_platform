# bi.post.reportForm_getReportInfoById.db9f04f8

详情
/

- 服务：bi；后端相对路径：`/reportForm/getReportInfoById`；方法：POST。
- 前端路径：/bi-docker/api/reportForm/getReportInfoById。
- 状态：frontend_only；操作：unverified；Schema：declared。
- 说明：前端有调用，本地后端无同方法/同路径声明；不可假定部署版本支持
- 前端源码：solar-engine-fe/src/api/modules/anasysisReport/index.ts:49；方法 detail；参数类型 `TReportId`。

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
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "string",
            "const": ""
          }
        ],
        "description": "报表主键ID"
      }
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
  "backend_type": "未匹配",
  "backend_schema": null,
  "frontend_schemas": [
    {
      "type": "object",
      "properties": {
        "searchConditionId": {
          "type": "number",
          "description": "报表对应的搜索条件id"
        },
        "menuName": {
          "type": "string",
          "description": "报表名称"
        },
        "userId": {
          "type": "number",
          "description": "创建人"
        },
        "productKey": {
          "type": "string",
          "description": "产品key"
        },
        "analyseType": {
          "type": "number",
          "description": "分析类型"
        },
        "appIds": {
          "type": "string",
          "description": "相关应用"
        },
        "isAllApp": {
          "type": "number"
        },
        "id": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "string",
              "const": ""
            }
          ],
          "description": "报表主键ID"
        },
        "searchCondition": {
          "type": "string",
          "description": "json,页面所选择的搜索条件"
        }
      },
      "required": [
        "searchCondition"
      ]
    }
  ]
}
```
