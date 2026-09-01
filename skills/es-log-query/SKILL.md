---
name: es-log-query
description: Query Elasticsearch logs and analyze operations issues. Use when Codex needs to inspect ES logs, discover unknown structured fields, inspect top field values, search by time range, keyword, level, traceId, requestId, Kubernetes metadata, run read-only schema/count diagnostics, or summarize incident evidence. Only supports read-only Elasticsearch operations.
metadata:
  version: "0.2.0"
---

# ES 日志查询

使用本 skill 查询 Elasticsearch 日志并分析运维问题。所有 ES 操作必须只读。

## 配置

运行时配置固定读取：

```text
~/.config/es-log-query/config.json
```

需要查看配置结构时，读取 `references/config-schema.md`。不要输出密码、认证头或完整配置文件。

## 标准流程

1. 明确 profile、index alias、时间范围、关键词、traceId、requestId 或业务现象。存在多个 profile 且用户未说明环境时，先确认 profile，避免静默查询默认环境。
2. 面对未知结构化日志，先运行 `discover`。它抽样 `_source`，但只输出字段路径、出现次数和字段能力，不输出样本值。
3. 根据发现结果，对 app、service、namespace、container、event、level、status 等低敏感 keyword 字段运行 `terms`，定位真实取值和分布。不要对用户标识、请求正文、token 或高基数字段运行 `terms`。
4. 用精确字段和值锁定目标后，先以 `size 5` 到 `size 20` 小样本验证查询条件，并用 `--source` 限制返回字段。
5. 条件确认后，再扩大到 `size 100` 到 `size 500`。需要趋势、多条件分类或非 terms 聚合时，使用 `--dsl`。
6. `discover` 未观察到目标字段时，用 `field-caps` 扩大字段 pattern；字段跨索引类型冲突或仍不确定时，再查看 `mapping`。
7. 输出结论时写清查询条件、时间范围、命中数量、代表性日志片段、判断依据和不确定性。

## 查询命令

```bash
node scripts/es-query.mjs search --profile prod --index app --start now-30m --end now --level error --message timeout --size 20
node scripts/es-query.mjs search --profile prod --index app --term traceId=abc123 --term "kubernetes.namespace_name.keyword=prod"
node scripts/es-query.mjs search --profile prod --index app --query-string 'level:error AND message:"timeout"'
node scripts/es-query.mjs search --profile prod --index app --dsl /tmp/query.json
```

常用参数：

- `--profile`：选择环境。省略时使用配置中的 `defaultProfile`。
- `--index`：索引别名或原始 index pattern。
- `--field-set`：字段映射集，默认 `default`。
- `--start`、`--end`：时间范围，支持 `now`、`now-30m`、ISO、秒级时间戳、毫秒级时间戳。
- `--message`：对 message 字段做全文匹配。
- `--level`：对 level 字段做短语匹配。
- `--term key=value`：精确匹配，可重复。
- `--match key=value`：全文匹配，可重复。
- `--query-string`：ES query_string 查询。
- `--dsl file.json`：读取完整 `_search` body。
- `--size`：返回条数，默认 100，最大 1000。
- `--source`：限制 `_source` 字段，使用逗号分隔。

## 诊断命令

```bash
node scripts/es-inspect.mjs profiles
node scripts/es-inspect.mjs indices --profile prod
node scripts/es-inspect.mjs discover --profile prod --index app --start now-1h --end now --query-string '"service-name"' --sample-size 10
node scripts/es-inspect.mjs terms --profile prod --index app --start now-1h --end now --field kubernetes.labels.app.keyword --size 20
node scripts/es-inspect.mjs terms --profile prod --index app --term kubernetes.labels.app.keyword=service-name --field event.keyword
node scripts/es-inspect.mjs mapping --profile prod --index app
node scripts/es-inspect.mjs field-caps --profile prod --index app --fields "@timestamp,message,level,kubernetes.*"
node scripts/es-inspect.mjs count --profile prod --index app --start now-1h --end now
```

`discover` 支持与查询命令相同的时间和过滤参数；`--sample-size` 默认 5、最大 20，`--max-fields` 默认 100、最大 200。`--max-fields` 限制样本字段数，相关 `.keyword` 等多字段会额外返回。结果中的 `presentInSamples` 是字段在样本中的出现次数，`aggregatable: true` 的 keyword／数值／日期字段适合后续 `terms` 或 DSL 聚合。

`terms` 使用 `--field` 指定任意可聚合字段，支持 `--term`、`--match`、`--query-string`、`--message`、`--level` 和时间范围；`--size` 默认 20、最大 100。它返回 top buckets，不代表字段的全部不同值。

## 分析输出格式

输出分析时使用以下结构：

1. 查询范围：profile、index、时间范围、核心条件。
2. 命中概况：total、returned、是否有聚合结果。
3. 关键证据：列出 2 到 5 条代表性日志，隐藏敏感字段。
4. 初步判断：说明最可能原因和依据。
5. 不确定性：说明还需要补充查询的方向。
6. 下一步建议：给出最小的后续查询或排查动作。

## 安全要求

- 只允许 `_search`、`_count`、`_mapping`、`_field_caps`。
- 不要尝试写入、删除、更新、bulk、reindex 或索引管理操作。
- `--dsl` 只能作为 `_search` body，不能改变请求路径或方法。
- 不要一次性大范围导出日志；默认 `size` 上限为 1000。
- `discover` 只输出字段结构，不输出内部抽样值；分析样本时继续使用 `--source` 最小化字段。
- `terms` 只用于业务分类和低敏感字段；输出前隐藏用户标识、请求标识、凭据及其他敏感 bucket。
- 查询失败或命中为 0 时，说明可能原因，包括字段、索引、时间范围、权限或网络。
