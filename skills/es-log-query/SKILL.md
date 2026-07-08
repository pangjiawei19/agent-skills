---
name: es-log-query
description: Query Elasticsearch logs and analyze operations issues. Use when Codex needs to inspect ES logs, search by time range, keyword, level, traceId, requestId, Kubernetes namespace, pod, container, app label, run read-only mapping/field-caps/count diagnostics, or summarize evidence for incident investigation. Only supports read-only Elasticsearch operations.
metadata:
  version: "0.1.0"
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

1. 明确 profile、index alias、时间范围、关键词、traceId、requestId、pod、namespace 或业务现象。
2. 字段不确定时，先运行 `scripts/es-inspect.mjs mapping` 或 `scripts/es-inspect.mjs field-caps`。
3. 先用 `size 5` 到 `size 20` 小样本验证查询条件。
4. 条件确认后，再扩大到 `size 100` 到 `size 500`。
5. 需要趋势或分类时，使用 `--dsl` 执行 `_search` 聚合。
6. 输出结论时写清查询条件、时间范围、命中数量、代表性日志片段、判断依据和不确定性。

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
node scripts/es-inspect.mjs mapping --profile prod --index app
node scripts/es-inspect.mjs field-caps --profile prod --index app --fields "@timestamp,message,level,kubernetes.*"
node scripts/es-inspect.mjs count --profile prod --index app --start now-1h --end now
```

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
- 查询失败或命中为 0 时，说明可能原因，包括字段、索引、时间范围、权限或网络。
