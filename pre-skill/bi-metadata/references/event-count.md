# 事件总次数

工具：`plugin__bi_metadata__SolarEventCount`。查询某产品单个事件的总次数，不是事件定义数、用户数或人均次数。

```json
{"product_key":"<当前产品业务键>","event_name":"_appEnd","date":"today"}
```

```json
{"product_key":"<当前产品业务键>","event_name":"_appEnd","date":"2026-10-20","end_date":"2026-10-25","time_zone":"Asia/Shanghai","app_ids":[123],"time_type":"server"}
```

- `date`：today/yesterday/YYYY-MM-DD；`end_date` 可选，范围包含首尾自然日，最多 31 天。
- `time_zone`：可选 IANA 时区；省略读取当前产品时区，再据此解析 today/yesterday，不使用 Runtime 本地日期。
- `app_ids`：可选真实应用数字 ID；省略表示产品全部应用。不能把 appCode/productKey 当作 appId。
- `time_type`：server/client；省略 server。用户特别要求客户端时间时传 client。
- 今天的结果是查询时刻已收集数据的总次数，今日尚未结束。

内部使用固定只读接口：产品时区 → 事件列表 → 指定事件属性与计算方式 → 事件分析。总次数必须从元数据识别为 `totalNumber/id=-1`；请求采用静态日期、合计、不分组、不显示阶段汇总、关闭近似计算。模型不能传入任意 URL、SQL、funcSqls、租户身份或凭据。

成功输出的业务实体在 `data`，例如：

```json
{"ok":true,"data":{"event_name":"_appEnd","count":42,"start_date":"2026-10-25","end_date":"2026-10-25","time_zone":"Etc/GMT-8","time_type":"server","all_apps":true,"stage":"completed"},"error":null}
```

数字 42 仅为格式示例。只有实际返回 count=0 才能回答 0 条。解析仅接受报表唯一总计行的 `event_0`；不使用报表 total、元数据长度、趋势猜测或空表推断数量。

失败时 `ok=false`、`data.count=null`；保留已确认的范围和 `error.stage`。report_query 失败可能包含 endpoint_id/http_status/upstream_code/request_id，用 request_id 定位上游日志。总耗时最多 25 秒，各阶段一次请求，不自动重试。失败后向用户说明没有取得数量及原因，结束本轮；不要读取全部接口、执行 Python 或继续反复换接口。

复杂属性筛选、分组、触发用户数及虚拟指标仍使用 [通用分析流程](workflows.md)。这些口径不在该工具范围内。
