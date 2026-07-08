# 配置说明

配置文件路径：

```text
~/.config/grafana-query/config.json
```

最小配置：

```json
{
  "defaultProfile": "prod",
  "profiles": {
    "prod": {
      "url": "https://grafana.example.com",
      "datasourceUid": "prometheus-main",
      "apiKey": "grafana-service-account-token",
      "timeoutSeconds": 15
    }
  }
}
```

字段说明：

- `defaultProfile`：未指定 `--profile` 时使用的 profile。
- `profiles.<name>.url`：Grafana URL，不需要尾部 `/`。
- `profiles.<name>.datasourceUid`：Grafana Prometheus datasource UID。
- `profiles.<name>.apiKey`：Grafana service account token。脚本不会打印该值。
- `profiles.<name>.timeoutSeconds`：HTTP 超时秒数，默认 15。

第一版只支持 JSON，不支持 YAML，不读取环境变量。
