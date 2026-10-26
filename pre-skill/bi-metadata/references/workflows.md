# 业务流程参考

接口 ID 以 SolarCatalog 实际返回为准。以下模板中的尖括号内容必须替换成已确认业务值；数字字段替换成 JSON 整数，不直接发送占位字符串。

## 查询某事件今天多少条

直接使用 `plugin__bi_metadata__SolarEventCount`，参数和失败处理见 [event-count.md](event-count.md)。这是总次数，不是事件定义数量或触发用户数。该流程不需要目录搜索、Python 或手工拼装 BehaviorViewModel。

## 查询产品事件与属性

1. 明确 product_key。查询 `/analysisBody/bodyList` 了解主体，查询 `/eventConfig/findByProductKey` 获取事件。
2. 用户需要事件属性时查询 `/profileType/findByProductKey`，用户属性使用 `/profileUser/findAllUserProfList`。自定义主体的 entityType/tableType 从主体结果取得，不能凭名称猜测。
3. 保留事件标识 eventName 与显示名 name，缺少显示名就说明未配置。元数据列表不能用于判断某天触发了多少次。
4. 根据 total 与实际 list 长度翻页；接口返回 pages=0 但 total>0 时仍应比较 total 和已取得数量。每页大小不超过 200。

## 行为分析

1. 确认日期区间、事件、计算口径、分析主体、应用范围、时区、分组及过滤条件。
2. 从事件、属性和计算方式接口取得 eventName/profileName/arithId/arithCode 等真实值；不要编造 SQL、虚拟事件表达式、指标公式和分析枚举。
3. 检索并 describe 对应的 `/report/eventAnalysis`、`funnelAnalysis`、`retentionAnalysis`、`traceAnalysis`、`scatterAnalysis` 或 `userPropertyAnalysis`。
4. 按 BehaviorViewModel 与实际前端调用构造 body。它可能包括 `behaviorContents`、`groups`、`filtrate`、`analysisBodyVo`、`startDate`、`endDate`、`timeType` 等；不要只传事件名就宣称完成分析。
5. 保持 query 中 showSql 等开关与 body 分开。一般无需请求 SQL，回答应解释业务指标。统计逻辑与单位以后端、真实返回和配置为准。

请求模板：

```json
{"endpoint_id":"bi.post.report_eventAnalysis.e914f96e","product_key":"<产品标识>","query":{"showSql":false},"body":{"productKey":"<产品标识>","startDate":"<确认后的起始日期>","endDate":"<确认后的结束日期>","behaviorContents":[{"eventName":"<从元数据取得>","arithId":"<从计算方式接口取得>","arithCode":"<从计算方式接口取得>"}],"groups":[],"filtrate":[]},"context":{},"path":{}}
```

模板只展示 JSON 的组织方式；具体主体、时间类型和所需嵌套字段以 describe 的契约与该分析页面为准。

## 报表、看板与模板

先列表/搜索定位 ID，再详情读取；不要用看板名称推算 ID。已有报表中保存的分析条件可以作为查询起点，但必须核对产品、主体、日期和应用范围。

编辑报表、看板布局、模板同步、删除或共享属于修改。先查询当前状态，再按用户要求提交必要字段，避免整份旧详情覆盖其他更新。文件导出在目录中有记录，当前工具不生成下载链接或假装已经下载。

## 分群与标签

先确认分析主体、动态/静态口径、日期和标签分类，查列表与详情，再查询结果。条件标签、指标标签、上传标签和结果标签属于不同创建流程，不能互换参数。

创建和刷新可能发起异步任务。提交成功不等于计算完成；按对应详情/状态接口核对任务结果后再回答。修改失败或超时先查标签或任务状态，避免重复创建。

## AB 实验查询与报告

1. 明确实际 appId。product_key 只确定产品权限，不能代替应用数字 ID。
2. 查询实验列表 `/portal/experiment/list`，按名称和状态定位 experimentId。列表参数包括 appId、name、status、experimentLayerId、pageNum/pageSize，具体类型以 describe 为准。
3. 读取实验详情及 `/portal/experiment/report/basicInfo`，确认时间、核心指标、实验组/对照组、分流主体与运行状态。
4. 读取报告 `/report/indSummary`、`/report/indDetailByDay`、`/report/retention`；日期和 indKey 由基本信息及用户要求确定。
5. 样本计算使用 `/report/sampleComputer`，不要拿指标列表元数据当作实验统计结果。结论要区分样本量、指标变化、置信区间或显著性字段；没有统计证据时不能断言实验胜出。

列表模板：

```json
{"endpoint_id":"rule.get.portal_experiment_list.09374427","product_key":"<产品标识>","query":{"appId":"<实际应用ID，替换为整数>","pageNum":1,"pageSize":20},"body":null,"context":{},"path":{}}
```

汇总模板：

```json
{"endpoint_id":"rule.post.portal_experiment_report_indSummary.189819d3","product_key":"<产品标识>","query":{},"body":{"experimentId":"<实验ID，替换为整数>","startDate":"<报告起始日期>","endDate":"<报告结束日期>","timeType":1,"showSql":false},"context":{},"path":{}}
```

timeType=1 在 Rule 源码中表示服务端时间；仅在用户口径与此一致时使用。趋势接口还需要实际 indKey，不能凭显示名称构造。

## AB 实验与实验层修改

- 创建/编辑：先查询参数、可用实验层、分流主体和可用流量，执行名称、参数和调试设备检查，按完整 DTO 提交。
- 上线：查询实验详情确认目标与状态。`GET .../setOnline` 是修改，使用 SolarMutate。
- 下线：先调用 `setOfflineCheck`，处理接口返回的参数或冲突要求，再根据用户指令提交 `setOffline`。
- 推全：先调用 `pushOutCheck`，核对胜出实验组、参数与流量目标，再提交 `pushOut`。
- 删除实验层：先调用 `checkExperiment`；接口 false 表示存在运行中/调试中的实验，不应继续删除。

源码中的状态值：1 暂存、2 调试中、3 运行中、4 已结束、5 删除。不要把这些枚举应用到其他模块的状态字段。

## 参数管理与配置下发

参数管理先查询 appId 下的参数列表、详情、AB 引用与规则引用。更新或删除前核对引用关系；不能只因参数名称相同就替换。

配置规则先查列表、详情、冲突规则/分组和状态。保存前执行 saveCheck；规则上线、下线、删除使用修改工具。初始化分组 ID 可能修改状态，不能当普通查询。

Rule 的 `/config/get`、签名下发、内部通知与 SDK 入口不是管理平台的业务代理，目录只提供参考。Agent 不模拟 SDK 设备身份或服务回调。
