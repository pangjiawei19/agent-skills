# 线上排障流程

## 标准流程

1. 运行 `profiles`，确认 profile。
2. 判断是否命中场景化 playbook。Pod 重启、Spring Boot WebFlux health/liveness、JVM 内存/GC、ReplicaSet 横向比较优先读取 `playbooks.md`。
3. 根据用户问题提取关键词，例如 `http`、`error`、`jvm`、`memory`、`gc`、`pod`、业务名。
4. 运行 `discover --keyword <关键词> --start <窗口>` 获取候选指标、labels 和 PromQL 草案。
   - 如果返回 `warnings[].code == "metadata_unavailable"`，不要中止；这表示 metadata 接口不可用，候选指标、labels 和 PromQL 草案仍可继续使用。
   - 如果 `discover` 本身不可用，改用 `list-metrics`、`labels`、`label-values` 组合探测。
5. 对最相关指标运行 `metadata`，确认 type 和 help。metadata 不可用时跳过，不要把 metadata 失败当作指标不存在。
6. 对指标运行 `labels`，确认可用 selector。已知 namespace、pod、service 等目标对象时加 `--selector label=value` 或 `--selector-re label=regex`。
7. 对关键 label 运行 `label-values`，确认具体取值。目标对象明确时必须使用 selector-aware 查询，例如：

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py label-values --metric http_server_requests_seconds_count --label uri --selector namespace=<namespace> --selector pod=<pod> --start <start> --end <end>
```
8. 用 `query` 验证 PromQL 是否有数据。
9. 用 `query-range` 查询时间窗口，并结合摘要分析。
10. 如判断异常，至少交叉查询一个相关指标验证，例如错误率配合 QPS、延迟配合 GC 或线程池、Pod CPU 配合 JVM CPU。
11. 需要分析先后关系时使用 `timeline` 把多个 PromQL 对齐到同一时间粒度，例如 uptime、heap、GC、QPS、max latency。

## 输出结论要求

结论必须包含：

- 查询 profile。
- 时间窗口。
- 使用的 PromQL。
- 关键数值，例如 avg、max、last。
- 异常维度，例如 uri、status、pod、instance。
- 不确定性和下一步建议。

## 无数据时

不要直接说“没有问题”。应检查：

- metric 名是否正确。
- label 名是否存在。
- label value 是否存在。
- 时间窗口是否覆盖问题发生时间。
- datasource profile 是否选错。

## 时间线对齐

`timeline` 用于把多条 PromQL range 查询合并成同一张时间表。每个 `--series` 使用 `name=promql` 格式；PromQL 最好提前聚合成单条序列，否则脚本只取第一条并给 warning。

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py timeline \
  --start <start> \
  --end <end> \
  --step 30 \
  --series 'uptime=process_uptime_seconds{namespace="<namespace>",pod="<pod>"}' \
  --series 'heap=sum(jvm_memory_used_bytes{namespace="<namespace>",pod="<pod>",area="heap"})' \
  --series 'qps=sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>"}[1m]))' \
  --format markdown
```
