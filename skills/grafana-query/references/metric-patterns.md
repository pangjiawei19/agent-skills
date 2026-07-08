# 常见指标族

这些只是搜索方向，不是固定契约。实际查询前必须通过 `list-metrics`、`metadata`、`labels`、`label-values` 验证。

## Spring Boot / Micrometer

常见关键词：

- `http_server_requests`
- `jvm_memory`
- `jvm_gc`
- `jvm_threads`
- `process_cpu`
- `system_cpu`
- `hikaricp`
- `tomcat`
- `reactor_netty`

常见 label：

- `application`
- `service`
- `instance`
- `uri`
- `method`
- `status`
- `exception`
- `outcome`

## HTTP

常见关键词：

- `http`
- `request`
- `requests`
- `duration`
- `latency`
- `seconds`

常见分析：

- QPS：优先查 counter 的 `rate(metric[5m])`。
- 错误率：按 `status`、`code`、`outcome` 聚合。
- 慢接口：按 `uri`、`route` 聚合耗时指标。

## JVM

常见关键词：

- `jvm_memory_used`
- `jvm_memory_committed`
- `jvm_gc_pause`
- `jvm_threads`
- `process_cpu_usage`

常见分析：

- 内存上涨：看 heap/nonheap、area、id。
- GC 异常：看 pause count、pause sum、max 或分位指标。
- 线程异常：看 live、daemon、blocked 等指标。

## Spring Boot WebFlux / Reactor Netty

常见关键词：

- `reactor_netty_eventloop_pending_tasks`
- `reactor_netty_http_server_response_time`
- `reactor_netty_http_server_connections`
- `reactor_netty_http_server_errors`
- `reactor_netty_http_client_response_time`
- `reactor_netty_connection_provider`

常见分析：

- Event loop 堵塞：看 `reactor_netty_eventloop_pending_tasks` 是否持续非 0 或持续升高。
- Server 侧连接压力：看 `reactor_netty_http_server_connections_active`。
- Server 侧错误：看 `reactor_netty_http_server_errors_total`。
- 下游慢调用：优先查 `reactor_netty_http_client_response_time_seconds_*`、`http_client_requests_seconds_*`。
- Health / liveness：先发现实际 URI，再查 `http_server_requests_seconds_count/sum/max`；不要假设一定是 `/actuator/health/liveness`。

## K8s / Pod

常见关键词：

- `container_cpu`
- `container_memory`
- `kube_pod`
- `kube_deployment`
- `kube_replicaset`
- `container_network`

常见 label：

- `namespace`
- `pod`
- `pod_name`
- `container`
- `cluster`
- `node`

## 自定义业务指标

优先使用业务关键词搜索，再通过 label 探测确认维度。不要假设自定义指标一定有 `service`、`pod`、`instance`。
