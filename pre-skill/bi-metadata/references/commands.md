# BI Metadata CLI 命令参考

所有示例在 `BiCli.arguments` 中按空格拆分成字符串数组传入。CLI 始终输出 JSON。

## 1. 分析主体列表

```bash
bi metadata analysis-bodies list --product-key <product_key>
```

必填参数：

- `--product-key`：BI 产品标识。

对应接口：`GET /analysisBody/bodyList`。

## 2. 事件列表

```bash
bi metadata events list \
  --product-key <product_key> \
  --page-num 1 \
  --page-size 50 \
  --search-text 登录 \
  --event-classify 1
```

可选参数：

- `--search-text`：按事件名称或事件标识搜索。
- `--event-classify`：事件分类编号，可以重复传入多个值。
- `--page-num`：页码，默认 1。
- `--page-size`：每页条数，默认 50，最大 200。

对应接口：`GET /eventConfig/findByProductKey`。

## 3. 用户属性列表

```bash
bi metadata user-properties list \
  --product-key <product_key> \
  --entity-type users
```

可选参数：

- `--entity-type`：分析主体字段，默认 `users`；自定义主体必须使用分析主体列表返回的字段。
- `--table-type`：自定义分析主体对应的表类型。
- `--profile-classify-list`：属性分类编号，多个编号使用英文逗号分隔。

不要根据用户的自然语言自行编造 `entity-type`。查询自定义主体时，应先执行分析主体列表命令。

对应接口：`GET /profileUser/findAllUserProfList`。

## 4. 事件属性列表

```bash
bi metadata event-properties list \
  --product-key <product_key> \
  --page-num 1 \
  --page-size 50 \
  --search-text 渠道 \
  --profile-classify 1 \
  --profile-type 2
```

可选参数：

- `--search-text`：按属性名称或属性标识搜索。
- `--profile-classify`：属性分类编号，可以重复传入。
- `--profile-type`：属性数据类型编号，可以重复传入。
- `--page-num`：页码，默认 1。
- `--page-size`：每页条数，默认 50，最大 200。

对应接口：`POST /profileType/findByProductKey`。

## 5. 指标列表

```bash
bi metadata metrics list \
  --product-key <product_key> \
  --page-num 1 \
  --page-size 50 \
  --search-text 付费 \
  --category 1
```

可选参数：

- `--category`：指标分类编号。
- `--search-text`：按指标名称搜索。
- `--sort-field-name`：服务端支持的排序字段。
- `--sort-type`：服务端支持的排序方式。
- `--page-num`：页码，默认 1。
- `--page-size`：每页条数，默认 50，最大 200。

对应接口：`GET /eventMetric/metricList`。

## 分页规则

当返回数据表示仍有下一页，并且用户需要完整结果时，按顺序继续查询：

```text
page-num=1 -> page-num=2 -> page-num=3
```

每次只增加一页，不并发请求大量页面。用户只要求查找某个名称时，优先使用 `--search-text`。
