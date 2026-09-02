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

日志字段结构不写入配置。查询默认使用 `@timestamp`、`message` 和 `level`；非标准时间字段使用 `--time-field`，其他结构化字段通过 `discover` 发现后使用通用过滤参数查询。

安全提醒：

- 不要提交这个配置文件。
- 不要把密码、认证头或完整配置贴到对话里。
- 如果需要让 Codex 检查配置，先脱敏 `password`。
