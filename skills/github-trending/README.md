# github-trending Skill

自动生成 GitHub Trending 热门项目分析报告。

## 安装

此 Skill 已内置于工作区，无需额外安装。

```bash
# 位置
~/.openclaw/workspace/skills/github-trending/
```

## 使用示例

### 基本用法

```
用户：拉取一下今天的 GitHub Trending
用户：看看 GitHub 上有什么热门项目
用户：GitHub Trending 今天什么项目火
```

### 带过滤条件

```
用户：只看 Python 项目的 GitHub Trending
用户：GitHub Trending 前端相关的
```

### 定时推送（可选）

可通过 cron 配置每日自动推送：

```json
{
  "name": "daily-github-trending",
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai" },
  "payload": { "kind": "agentTurn", "message": "生成今天的 GitHub Trending 报告" }
}
```

## 文件结构

```
github-trending/
├── SKILL.md              # Skill 主文档（触发条件、使用说明）
├── github-trending.js    # 辅助脚本（解析逻辑）
├── example-output.md     # 输出格式示例
└── README.md             # 本文件
```

## 输出内容

1. **项目列表**（默认 Top 10）
   - 排名
   - 项目名称（带超链接）
   - 总 Star 数 + 今日新增
   - 主要编程语言
   - 项目描述（中文）

2. **趋势分析**
   - 热门关键词
   - 技术栈分布
   - 观察与洞察

## 注意事项

- 需要 browser 工具支持（访问 GitHub 页面）
- 网络环境需能访问 GitHub
- 报告基于当日数据，具有时效性

## 维护者

🦐 小虾米

## 更新日志

- 2026-03-16: 初始版本，支持基本报告生成和趋势分析
