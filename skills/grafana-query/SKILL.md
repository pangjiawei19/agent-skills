---
name: grafana-query
description: Query Grafana Prometheus datasources and analyze online operations issues. Use when the user asks Codex to 查询 Grafana、查看指标、分析线上问题、排查 Spring Boot/JVM/HTTP/K8s/Pod/自定义业务指标、拼 PromQL selector、发现 metric 或 label、获取 Grafana 指标数据。
metadata:
  version: 0.1.0
---

# grafana-query

使用 Grafana datasource proxy 查询 Prometheus 指标，并辅助分析线上问题。

## 必须遵守

1. 先发现指标和 label，再拼 PromQL；不要直接凭经验猜 selector。
2. 如用户未指定 profile，先运行 `profiles` 查看默认 profile 和可用 profile。
3. 排障时优先用 `discover`、`list-metrics`、`metadata`、`labels`、`label-values` 缩小范围。
4. 拼好 PromQL 后，先用 `query` 验证是否有数据，再用 `query-range` 查询目标时间窗口。
5. 输出结论必须包含时间窗口、PromQL、关键数值、异常 label 维度和不确定性。
6. 不要输出 Grafana `apiKey`。
7. 遇到 Pod 重启、Spring Boot WebFlux health/liveness、JVM 内存/GC、ReplicaSet 横向比较时，先读取 `references/playbooks.md` 选择对应 playbook。
8. 目标对象明确时，优先使用 `--selector` / `--selector-re` 缩小指标发现范围，避免被全局 label values 干扰。
9. 需要关联多个指标的先后关系时，使用 `timeline` 对齐时间线，再下结论。

## 脚本

脚本路径：

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py
```

常用命令：

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py profiles
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py discover --profile prod --keyword http --start -1h
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py labels --profile prod --metric http_server_requests_seconds_count --start -1h
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py label-values --profile prod --metric http_server_requests_seconds_count --label uri --start -1h
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py label-values --metric http_server_requests_seconds_count --label uri --selector namespace=prod --selector pod=api-xxx --start -1h
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py discover --keyword http --selector namespace=prod --selector pod=api-xxx --start -1h
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py query-range --profile prod --promql 'sum(rate(http_server_requests_seconds_count[5m])) by (uri)' --start -1h --step 60
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py timeline --start -15m --step 30 --series 'uptime=process_uptime_seconds{pod="api-xxx"}' --series 'qps=sum(rate(http_server_requests_seconds_count{pod="api-xxx"}[1m]))' --format markdown
```

## 参考文件

- 配置文件格式：读取 `references/config.md`。
- 排障流程：读取 `references/workflow.md`。
- 常见指标族：读取 `references/metric-patterns.md`。
- 场景化排障模板：遇到 Pod 重启、Spring Boot WebFlux、JVM 压力或横向比较时读取 `references/playbooks.md`。
