# ES 日志查询配置

配置文件固定放在：

```text
~/.config/es-log-query/config.json
```

示例：

```json
{
  "defaultProfile": "prod",
  "profiles": {
    "prod": {
      "node": "https://es.example.com:9200",
      "auth": {
        "username": "elastic",
        "password": "xxx"
      },
      "requestTimeoutMs": 30000,
      "insecure": false,
      "indices": {
        "app": "app-log-*",
        "nginx": "nginx-*"
      },
      "fieldSets": {
        "default": {
          "time": "@timestamp",
          "message": "message",
          "level": "level",
          "traceId": "traceId",
          "requestId": "requestId",
          "namespace": "kubernetes.namespace_name.keyword",
          "pod": "kubernetes.pod_name.keyword",
          "container": "kubernetes.container_name.keyword",
          "app": "kubernetes.labels.app.keyword",
          "stream": "containerd_stream"
        },
        "containerd": {
          "time": "containerd_time",
          "message": "message",
          "level": "level"
        }
      }
    }
  }
}
```

字段说明：

- `defaultProfile`：默认环境名。命令未传 `--profile` 时使用。
- `profiles`：环境配置表。
- `node`：ES 地址。
- `auth.username`、`auth.password`：Basic Auth 凭证。
- `requestTimeoutMs`：请求超时时间，单位毫秒。
- `insecure`：HTTPS 是否跳过证书校验。
- `indices`：索引别名。命令中的 `--index app` 会解析成对应 pattern。
- `fieldSets`：字段映射集。`default` 是默认映射。

安全提醒：

- 不要提交这个配置文件。
- 不要把密码、认证头或完整配置贴到对话里。
- 如果需要让 Codex 检查配置，先脱敏 `password`。
