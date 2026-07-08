# 场景化排障 Playbook

这些 playbook 用于把 Grafana 查询组织成可复用的排障路径。先按场景选择 playbook，再结合实际 metric、label 和时间窗口微调 PromQL。不要把模板当成固定事实；每次查询前仍要用 `labels`、`label-values` 或一次小范围 `query` 验证 selector 有数据。目标对象明确时优先使用 `--selector` / `--selector-re` 做指标发现。

## Pod 重启

适用场景：用户给出 namespace、pod、异常时间，想判断重启原因。

### 查询顺序

1. 确认重启时间：

```promql
increase(kube_pod_container_status_restarts_total{namespace="<namespace>",pod="<pod>"}[15m])
```

```promql
process_uptime_seconds{namespace="<namespace>",pod="<pod>"}
```

2. 查询 K8s termination reason：

```promql
kube_pod_container_status_last_terminated_reason{namespace="<namespace>",pod="<pod>"}
```

3. 判断是否 OOMKilled：

```promql
container_memory_working_set_bytes{namespace="<namespace>",pod="<pod>",container!=""}
```

```promql
increase(container_memory_failures_total{namespace="<namespace>",pod="<pod>",container!="",failure_type=~"pgmajfault|pgfault"}[2m])
```

4. 交叉验证 JVM、CPU、HTTP 和日志：

```promql
sum(rate(container_cpu_usage_seconds_total{namespace="<namespace>",pod="<pod>",container!=""}[2m])) by (container)
```

```promql
sum(jvm_memory_used_bytes{namespace="<namespace>",pod="<pod>",area="heap"})
```

```promql
sum(increase(jvm_gc_pause_seconds_count{namespace="<namespace>",pod="<pod>"}[1m])) by (action,cause)
```

```promql
topk(20, sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>"}[1m])) by (uri,status,exception))
```

```promql
sum(increase(log4j2_events_total{namespace="<namespace>",pod="<pod>"}[1m])) by (level)
```

5. 对齐关键指标时间线：

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py timeline \
  --start <start> \
  --end <end> \
  --step 30 \
  --series 'uptime=process_uptime_seconds{namespace="<namespace>",pod="<pod>"}' \
  --series 'heap=sum(jvm_memory_used_bytes{namespace="<namespace>",pod="<pod>",area="heap"})' \
  --series 'gc_high_usage=sum(increase(jvm_gc_pause_seconds_count{namespace="<namespace>",pod="<pod>",cause="High Usage"}[1m]))' \
  --series 'qps=sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>"}[1m]))' \
  --format markdown
```

### 判断边界

- `reason="OOMKilled"` 才能直接支持 K8s OOMKilled；`reason="Error"` 只能说明容器非正常退出。
- 没有 exit code 时，不要断言是 `137` 或 liveness kill。
- `process_uptime_seconds` 归零是应用进程重启的强证据。
- 容器 working set 未达到 limit，不代表 Java heap 没有压力；要同时看 `jvm_memory_used_bytes` 和 `jvm_memory_max_bytes`。
- HTTP 5xx 不升高，不代表业务无异常；慢请求、UNKNOWN、日志 WARN 也可能是关键线索。

## Spring Boot WebFlux Health / Liveness

适用场景：怀疑 WebFlux 应用 health check 无法响应，导致 K8s liveness probe kill。

### 查询顺序

1. 发现 health 相关 URI：

```bash
python3 /Users/pangjiawei/.agents/skills/grafana-query/scripts/grafana_query.py label-values \
  --metric http_server_requests_seconds_count \
  --label uri \
  --selector namespace=<namespace> \
  --selector pod=<pod> \
  --start <start> \
  --end <end>
```

重点找：`/actuator/health`、`/actuator/health/liveness`、`/actuator/health/readiness`、`/healthy`、`/uptime`。

2. 查询 health 请求状态与请求量：

```promql
sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>",uri=~"/actuator/health.*|/healthy|/uptime"}[1m])) by (uri,status,exception,outcome)
```

3. 查询 health 请求平均耗时和最大耗时：

```promql
sum(rate(http_server_requests_seconds_sum{namespace="<namespace>",pod="<pod>",uri=~"/actuator/health.*|/healthy|/uptime"}[1m])) by (uri,status)
/
sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>",uri=~"/actuator/health.*|/healthy|/uptime"}[1m])) by (uri,status)
```

```promql
max(http_server_requests_seconds_max{namespace="<namespace>",pod="<pod>",uri=~"/actuator/health.*|/healthy|/uptime"}) by (uri,status)
```

4. 查询 WebFlux event loop 是否堵塞：

```promql
max(reactor_netty_eventloop_pending_tasks{namespace="<namespace>",pod="<pod>"}) by (name)
```

```promql
sum(reactor_netty_http_server_connections_active{namespace="<namespace>",pod="<pod>"})
```

```promql
sum(rate(reactor_netty_http_server_errors_total{namespace="<namespace>",pod="<pod>"}[1m])) by (remote_address)
```

5. 查询活跃请求是否堆积：

```promql
sum(http_server_requests_active_seconds_count{namespace="<namespace>",pod="<pod>"}) by (uri)
```

### 判断边界

- health URI 只有 200 且耗时毫秒级时，不支持“health endpoint 自己持续失败”。
- 已完成的 health 请求成功，不等于完全排除 liveness failure；被 kubelet kill 前未完成的 probe 可能不会进入 Micrometer。
- `reactor_netty_eventloop_pending_tasks` 长时间非 0 或持续升高，才更支持 WebFlux event loop 堵塞。
- 要确认 liveness kill，最好补 Kubernetes event：`Liveness probe failed`、`Killing container`、exit code。

## JVM 内存 / GC 压力

适用场景：怀疑 Java 进程因为 heap 压力、GC 或 OOM 异常退出。

### 查询顺序

1. 查询 heap 上限与使用量：

```promql
sum(jvm_memory_max_bytes{namespace="<namespace>",pod="<pod>"}) by (area)
```

```promql
sum(jvm_memory_used_bytes{namespace="<namespace>",pod="<pod>"}) by (area)
```

2. 查询 GC 次数：

```promql
sum(increase(jvm_gc_pause_seconds_count{namespace="<namespace>",pod="<pod>"}[1m])) by (action,cause)
```

3. 如果 `jvm_gc_pause_seconds_sum` 有有效值，查询 GC pause 时长：

```promql
sum(increase(jvm_gc_pause_seconds_sum{namespace="<namespace>",pod="<pod>"}[1m])) by (action,cause)
```

4. 查询线程状态：

```promql
sum(jvm_threads_states_threads{namespace="<namespace>",pod="<pod>"}) by (state)
```

5. 关联业务入口：

```promql
topk(20, sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod="<pod>"}[1m])) by (uri,status))
```

```promql
topk(20, max(http_server_requests_seconds_max{namespace="<namespace>",pod="<pod>"}) by (uri,status))
```

### 判断边界

- heap used 接近 heap max，且 `High Usage` GC 明显升高，是 JVM 堆压力强信号。
- `jvm_gc_pause_seconds_count` 升高但 `sum` 为 0 时，只能说明 GC 次数，不要推断具体 STW 时长。
- Java heap 压力可能先表现为慢请求、UNKNOWN、WARN 激增，而不一定表现为 HTTP 5xx。

## 横向比较 ReplicaSet

适用场景：判断问题是单 Pod、单节点，还是同组服务共同压力。

常用 PromQL：

```promql
increase(kube_pod_container_status_restarts_total{namespace="<namespace>",pod=~"<replicaset-prefix>.*"}[15m])
```

```promql
sum(jvm_memory_used_bytes{namespace="<namespace>",pod=~"<replicaset-prefix>.*",area="heap"}) by (pod)
```

```promql
sum(increase(jvm_gc_pause_seconds_count{namespace="<namespace>",pod=~"<replicaset-prefix>.*"}[2m])) by (pod,cause)
```

```promql
sum(rate(http_server_requests_seconds_count{namespace="<namespace>",pod=~"<replicaset-prefix>.*"}[1m])) by (pod)
```

```promql
kube_pod_created{namespace="<namespace>",pod=~"<replicaset-prefix>.*"}
```

判断边界：

- 同 ReplicaSet 多个老 Pod 同时高 QPS、高 heap 或重启，优先考虑服务整体压力、上游流量、下游依赖。
- 新创建 Pod 样本少，不能直接和老 Pod 的长期指标等价比较。
