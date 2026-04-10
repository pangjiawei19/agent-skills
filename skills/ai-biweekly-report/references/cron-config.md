# AI 工程半月报 Cron 自动化配置

## 自动化目标

- **上半月报**：每月 16 号上午 9:00 自动生成（覆盖 1-15 日）
- **下半月报**：次月 1 号上午 9:00 自动生成（覆盖 16-月底）
- **自动推送**：飞书文档 + 消息通知

## Cron 配置

### 上半月报配置

```json
{
  "name": "AI 工程半月报 - 上半月",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 16 * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请生成 {{current_year}} 年 {{current_month}} 月上半月 AI 工程半月报（{{current_month}} 月 1 日 -15 日），按照 ai-biweekly-report 技能流程执行。",
    "timeoutSeconds": 1800
  },
  "sessionTarget": "isolated",
  "enabled": true,
  "delivery": {
    "mode": "announce",
    "channel": "feishu"
  }
}
```

### 下半月报配置

```json
{
  "name": "AI 工程半月报 - 下半月",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 1 * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请生成 {{previous_month}} 月下半月 AI 工程半月报（{{previous_month}} 月 16 日 -{{last_day}} 日），按照 ai-biweekly-report 技能流程执行。",
    "timeoutSeconds": 1800
  },
  "sessionTarget": "isolated",
  "enabled": true,
  "delivery": {
    "mode": "announce",
    "channel": "feishu"
  }
}
```

## 设置步骤

### Step 1: 使用 cron.add 创建任务

```bash
# 上半月报
cron add --name "AI 工程半月报 - 上半月" \
  --schedule "0 9 16 * *" \
  --payload "agentTurn:生成 AI 工程半月报" \
  --session-target isolated

# 下半月报
cron add --name "AI 工程半月报 - 下半月" \
  --schedule "0 9 1 * *" \
  --payload "agentTurn:生成 AI 工程半月报" \
  --session-target isolated
```

### Step 2: 验证配置

```bash
cron list
```

预期输出：
```
✓ AI 工程半月报 - 上半月 (0 9 16 * *) - enabled
✓ AI 工程半月报 - 下半月 (0 9 1 * *) - enabled
```

### Step 3: 测试运行（可选）

```bash
# 手动触发一次测试
cron run --job-id <job_id>
```

## 时区说明

- **Asia/Shanghai** (UTC+8)：适合中国用户
- 上半月报：北京时间 16 号 17:00（UTC 9:00）
- 下半月报：北京时间 1 号 17:00（UTC 9:00）

## 超时设置

- **timeoutSeconds**: 1800 (30 分钟)
- 原因：搜索 + 核实 + 分析 + 生成文档预计需要 20-30 分钟

## 交付设置

- **delivery.mode**: "announce"（推送到飞书）
- **delivery.channel**: "feishu"（飞书渠道）

## 监控和维护

### 检查运行历史

```bash
cron runs --job-id <job_id>
```

### 常见问题

1. **任务执行失败**
   - 检查：飞书授权是否有效
   - 检查：网络连通性
   - 解决：重新授权或手动执行

2. **生成内容质量下降**
   - 检查：搜索关键词是否需要更新
   - 检查：数据源是否有变化
   - 解决：更新技能配置

3. **文档创建失败**
   - 检查：飞书 API 限流
   - 解决：稍后重试或手动创建

## 禁用/启用任务

### 临时禁用

```bash
cron update --job-id <job_id> --patch '{"enabled": false}'
```

### 重新启用

```bash
cron update --job-id <job_id> --patch '{"enabled": true}'
```

## 删除任务

```bash
cron remove --job-id <job_id>
```

## 自定义配置

### 更改报告周期

如果想改为**周报**（每周一上午 9 点）：

```json
{
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * 1"
  }
}
```

### 更改交付渠道

如果想通过**邮件**发送：

```json
{
  "delivery": {
    "mode": "webhook",
    "to": "https://your-email-webhook.com/send"
  }
}
```

### 添加多个通知渠道

```json
{
  "delivery": {
    "mode": "announce",
    "channel": "feishu",
    "targets": ["user:ou_xxx", "chat:oc_xxx"]
  }
}
```

## 成本估算

### API 调用次数（每次报告）

| 操作 | 次数 | 说明 |
|------|------|------|
| web_search | 8-10 次 | 8 大数据源 |
| web_fetch | 20-30 次 | 候选资讯日期核实 |
| feishu_create_doc | 1 次 | 创建文档 |
| message.send | 1 次 | 发送摘要 |
| **总计** | **30-42 次** | |

### 月度成本

- **执行次数**：2 次/月
- **API 调用**：60-84 次/月
- **Token 消耗**：约 50K-100K tokens/月
- **预计成本**：$0.5-$2/月（取决于模型定价）

## 最佳实践

1. **首次执行后检查质量**：手动审查 1-2 次自动生成的报告
2. **定期更新搜索关键词**：每季度审查一次数据源和关键词
3. **收集用户反馈**：哪些资讯最有价值，调整筛选策略
4. **监控失败率**：如连续失败 2 次，检查配置和网络
5. **保留手动触发能力**：特殊情况可手动生成

---

*配置版本：v1.0 | 创建日期：2026-03-17*
