---
name: github-trending
description: "抓取 GitHub Trending 热门仓库，输出含排名/项目名/总 Star/今日新增/语言/中文描述的项目列表，并做趋势洞察。当用户说'拉一下 GitHub Trending'、'今天 GitHub 热门'、'GitHub 趋势'、'看看 GitHub 上火了啥'、'GitHub 周榜/月榜'、'只看 Python 的 Trending'，或要求生成 GitHub 每日/每周热门项目报告时触发。"
---

# github-trending - GitHub Trending 抓取技能

🦐 抓取 GitHub Trending 页面，输出格式化项目列表 + 趋势洞察

---

## 触发条件

用户说出以下或语义相近的表述时触发：
- "拉一下 GitHub Trending" / "今天 GitHub 热门"
- "GitHub 趋势 / 周榜 / 月榜"
- "看看 GitHub 上有什么新项目"
- "只看 Python / TypeScript 的 Trending"（带语言过滤）
- Cron 定时任务（见下方配置示例）

---

## 功能

1. 抓取 GitHub Trending 页面（日榜 / 周榜 / 月榜，可按语言过滤）
2. 每个仓库提取：排名、owner/repo、总 Star、今日（或周期内）新增 Star、主语言、描述（翻译为中文）
3. 默认取前 10 个，可根据用户需求调整（上限 25，即 Trending 页一屏）
4. 基于当期数据生成趋势洞察（热点方向、语言分布、值得关注的项目）

---

## 使用方式

### 基础用法
```
拉一下今天的 GitHub Trending
```

### 指定周期
```
看看本周 GitHub 热门项目     → since=weekly
GitHub 本月趋势             → since=monthly
```

### 语言过滤
```
只看 Python 的 Trending      → /trending/python
前端相关的 Trending          → /trending/typescript (或 javascript)
```

### Cron 定时任务
```yaml
sessionTarget: "main"
payload:
  kind: "systemEvent"
  text: "执行 github-trending 技能，抓取今日 Top 10"
```

---

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `count` | 10 | 输出条数（1-25） |
| `since` | `daily` | `daily` / `weekly` / `monthly` |
| `language` | 无 | 语言过滤，如 `python`、`typescript`、`rust` |

**URL 拼装规则：**

| 需求 | URL |
|------|-----|
| 今日所有语言 | `https://github.com/trending` |
| 本周所有语言 | `https://github.com/trending?since=weekly` |
| 今日 Python | `https://github.com/trending/python` |
| 本月 Rust | `https://github.com/trending/rust?since=monthly` |

---

## 实施步骤

### 1. 抓取页面 HTML（首选 `web_fetch`）

GitHub Trending 是纯 SSR 页面，所有仓库信息都在初始 HTML 中，直接 `web_fetch` 最快最稳：

```
web_fetch "https://github.com/trending"
```

> 未登录也可访问，无需处理 cookie。偶发 429（限流）时重试 1 次，仍失败走回退方案。

### 2. 备选：浏览器快照

若 `web_fetch` 返回空列表或被限流拦截，用 `browser` 回退：
1. `browser` 打开目标 URL
2. `browser.snapshot` 取 aria 结构化快照

### 3. 解析仓库列表

Trending 页面每个仓库是一个 `<article class="Box-row">`，自上而下即为当前排序。每个 article 包含：

| 字段 | 位置 |
|------|------|
| `owner/repo` | `<h2>` 内的 `<a href="/owner/repo">` |
| 描述 | `<p class="col-9 color-fg-muted">` 文本 |
| 主语言 | `<span itemprop="programmingLanguage">` |
| 总 Star | 第一个带 star 图标的 `<a href="/owner/repo/stargazers">` 文本 |
| 周期新增 Star | `<span class="d-inline-block float-sm-right">` 文本（如 "1,234 stars today"） |

### 4. 逐条提取字段

**必填字段：** owner、repo、总 Star、URL
**可选字段：** 语言（部分 repo 无语言标签，如纯文档/纯 shell 脚本仓库）、描述（少数 repo 为空）、周期内新增（冷门榜单位置可能为 0 或缺失）

**字段缺失处理：**

- 语言缺失 → 显示为 `N/A`，不报错（Trending 本身就允许无语言 repo 上榜）
- 描述缺失 → 显示为 `（无描述）`，不报错
- 周期新增 Star 缺失或为 0 → 显示 `+0`，不报错
- owner/repo/总 Star 缺失 → 页面结构可能改版，走 [失败处理](#失败处理)

### 5. 描述翻译

把 GitHub 上的英文描述翻译成中文，原则：

- **技术专有名词不译**：Agent、Framework、SDK、API、LLM、RAG、MCP、Transformer、Kubernetes 等保留英文
- **项目名/厂商名不译**：Claude Code、OpenAI、Anthropic 等保留原文
- **emoji 保留**：原描述中的 emoji 直接保留
- **简洁优先**：GitHub 描述通常一句话，翻译后也保持一句话，不扩写
- **原文已是中文则不处理**：直接用原文

示例：
- `"A headless browser designed for AI and automation"` → `"专为 AI 和自动化设计的无头浏览器"`
- `"Agent skills framework and software development methodology"` → `"Agent 技能框架与软件开发方法论"`

### 6. 格式化输出

先列项目清单，再做趋势分析。汇总行放最前面。

```
**GitHub Trending - 今日 Top 10** 🦐

---

**1. repo-name** ⭐ 27,989 (+2,782 今日)
- **链接：** [owner/repo](https://github.com/owner/repo)
- **语言：** Python
- **描述：** 中文描述

---

**2. ...**

---

## 📊 趋势洞察

### 🔥 热点方向
（从描述中动态提炼 2-3 个本期集中出现的方向，带项目数）

### 🧱 语言分布
（所有上榜项目的语言统计，按项目数排序）

### 💡 值得关注
（挑 1-3 个有代表性的项目点评，例如：冷门语言上榜、新兴领域、大厂开源等）
```

**汇总行根据实际周期/语言调整：**
- 今日 Top 10 → `**GitHub Trending - 今日 Top 10** 🦐`
- 本周 Python Top 10 → `**GitHub Trending - 本周 Python Top 10** 🦐`

### 7. 生成趋势洞察

**热点方向**（重点）：不要用写死的关键词表，而是读一遍 10 个项目的描述，自己归纳出本期集中出现的 2-3 个方向。例如：

- 若 10 个项目里有 6 个都在做 Agent / Coding Agent 基础设施 → "**AI Agent 基础设施**（6/10）"
- 若出现多个 RAG / 向量数据库 / 长上下文项目 → "**检索增强与长上下文**（3/10）"
- 若出现多个特定厂商相关生态（如 Claude Code / MCP） → 单独点出来

GitHub Trending 热点轮换快（今天 MCP、下周 Agent、下月又是新架构），写死词表一周就失效，由模型动态归纳更鲁棒。

**值得关注**：不是简单的"最热项目 = 第一名"，而是挑有信号价值的点——

- 冷门语言上榜（Zig / Gleam / Mojo 等）
- 新兴领域首次出现（如某个新协议的第一波实现）
- 大厂开源新项目
- 单日暴涨（今日增长 > 2000 星通常是有话题性的事件）

---

## 失败处理

- **web_fetch 返回空或 HTML 无 `Box-row`**：走 browser 回退，仍失败返回明确错误，不静默降级
- **必填字段缺失（owner/repo/总 Star）**：说明 GitHub 改版，打印具体缺失字段 + article HTML 片段，提示需更新解析规则
- **可选字段缺失（语言/描述/今日新增）**：按 [第 4 步](#4-逐条提取字段) 规则降级显示，不报错
- **429 限流**：重试 1 次（间隔 5 秒），仍失败返回"GitHub 限流，请稍后重试"
- **count 大于页面实际项目数**：输出实际条数并提示"GitHub Trending 当日仅 N 条"

---

## 示例输出

参考 [`example-output.md`](./example-output.md) 获取完整输出样例（含字段缺失的降级写法与趋势洞察格式）。

---

## 扩展方向

1. Trending Developers 榜（`/trending/developers`）
2. 多语言并行抓取后对比
3. 历史趋势追踪（连续上榜几天 / 是否从日榜晋级到周榜）
4. 导出飞书文档 / 推送飞书消息

---

## 依赖工具

- `web_fetch` - 首选，拉取 Trending 页面 HTML
- `browser` / `browser.snapshot` - 回退方案，处理限流或页面改版场景

---

_最后更新：2026-04-20_

**更新记录：**
- 2026-04-20：对齐 infoq-digest 规范——补 frontmatter、改 `web_fetch` 首选、补实施步骤（含字段降级规则与描述翻译策略）、补失败处理；移除伪代码 `.js` 脚本与内容重复的 README.md；趋势洞察去掉硬编码关键词表，改由模型动态归纳
- 2026-03-16：初始版本
