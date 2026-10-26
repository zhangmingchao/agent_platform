# bi.post.maxAgent_question.d73ad470

发送问题
 新会话：不传 sessionId
/

- 服务：bi；后端相对路径：`/maxAgent/question`；方法：POST。
- 前端路径：/bi-docker/api/maxAgent/question。
- 状态：frontend_only；操作：unverified；Schema：declared。
- 说明：前端有调用，本地后端无同方法/同路径声明；不可假定部署版本支持
- 前端源码：solar-engine-fe/src/api/modules/maxAgent/index.ts:31；方法 question；参数类型 `{ question: string; sessionId?: number | undefined; productKey: string; requestId: string; }`。

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
      "question": {
        "type": "string"
      },
      "sessionId": {
        "type": "number"
      },
      "productKey": {
        "type": "string"
      },
      "requestId": {
        "type": "string"
      }
    },
    "required": [
      "question",
      "productKey",
      "requestId"
    ]
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
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
