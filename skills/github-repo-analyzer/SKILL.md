---
name: github-repo-analyzer
description: GitHub 仓库分析工具。当用户提供 GitHub repo 链接时，自动抓取 README 并生成结构化分析报告（核心功能、使用场景、快速开始、技术栈），支持将分析结果保存到飞书多维表格。使用场景：(1) 用户看到 GitHub Trending 推送后想快速了解某个 repo，(2) 用户提供 GitHub 链接要求分析，(3) 需要将 repo 分析结果记录到收藏表格。
---

# GitHub Repo Analyzer

快速分析 GitHub 仓库，生成结构化摘要，辅助决策是否值得深入阅读。

## 核心流程

### 1. 接收 repo 链接

用户会提供 GitHub 链接，格式如：
- `https://github.com/owner/repo`
- `github.com/owner/repo`
- `owner/repo`

### 2. 抓取 README

使用 `web_fetch` 工具抓取 README 内容：

```bash
web_fetch url="https://raw.githubusercontent.com/{owner}/{repo}/main/README.md" extractMode="markdown"
```

如果 `main` 分支不存在，尝试 `master` 分支。

### 3. AI 分析总结

基于 README 内容，生成以下结构化信息：

**分析维度：**
1. **核心功能**（1-2 句话）：这个 repo 是做什么的？解决什么问题？
2. **使用场景**：适合什么场景使用？目标用户是谁？
3. **快速开始**：如何安装/使用？（提取关键命令或代码片段）
4. **技术栈**：主要编程语言、框架、依赖
5. **推荐指数**：高/中/低（基于实用性、文档质量、活跃度）

**输出格式：**
~~~markdown
### 📦 {repo 名称}

**核心功能：** 1-2 句话总结

**使用场景：**
- 场景 1
- 场景 2

**快速开始：**
```bash
# 安装命令
# 使用示例
```

**技术栈：** Python, TypeScript, ...

**推荐指数：** 高/中/低

**项目链接：** https://github.com/owner/repo
~~~

### 4. 保存到飞书多维表格

**表格信息：**
- 表格 URL：https://magictavern.feishu.cn/base/UU99brPBfa7ECrsOjgqc2XZDnXf
- App Token：`UU99brPBfa7ECrsOjgqc2XZDnXf`
- 表 ID：`tbl0AV08vsL2pZPK`

**字段映射：**
| 字段名 | 字段 ID | 值 |
|--------|--------|-----|
| Repo 名称 | fldZ1AzHdC | `{owner}/{repo}` |
| GitHub 链接 | fldsdPtyca | 完整 URL |
| 标记时间 | fldPmruhgW | 当前时间戳（毫秒） |
| AI 分析摘要 | fldqOFQhIb | 步骤 3 生成的分析文本 |
| 状态 | fldquBsrOd | "已分析" |
| 技术栈 | fldEpFIoZl | 数组，如 `["Python", "AI/ML"]` |
| 优先级 | fld4ya34Ko | "高"/"中"/"低" |

**创建记录：**
```bash
feishu_bitable_app_table_record action="create" app_token="UU99brPBfa7ECrsOjgqc2XZDnXf" table_id="tbl0AV08vsL2pZPK" fields={...}
```

### 5. 返回结果

向用户返回：
1. 分析摘要（直接在消息中展示）
2. 表格记录链接（方便后续查看）

## 技术栈识别规则

从 README 中识别技术栈的关键词：

| 关键词 | 映射到 |
|--------|--------|
| Python, pip, django, flask | Python |
| JavaScript, JS, Node.js, npm | JavaScript |
| TypeScript, TS, tsx | TypeScript |
| Go, Golang | Go |
| Rust, cargo, crate | Rust |
| Java, Maven, Gradle | Java |
| AI, ML, 机器学习，深度学习，LLM | AI/ML |
| React, Vue, Angular | JavaScript |
| 其他 | Other |

## 优先级判断规则

**高优先级：**
- 解决明确痛点，有实际应用场景
- 文档清晰，快速开始示例完整
- Star 增长快（近期热门）
- 与用户当前项目/学习方向相关

**中优先级：**
- 功能有用但非必需
- 文档一般，需要摸索使用
- 技术栈与用户相关但非核心

**低优先级：**
- 功能重复，已有替代方案
- 文档缺失，学习成本高
- 纯实验性项目，无实际应用价值

## 错误处理

1. **README 不存在**：告知用户"该 repo 没有 README，无法分析"
2. **链接格式错误**：提示用户提供正确的 GitHub 链接
3. **飞书写入失败**：先展示分析结果，稍后重试写入

## 使用示例

**用户输入：**
```
分析一下这个：https://github.com/openai/whisper
```

**你的处理：**
1. 提取 `openai/whisper`
2. 抓取 `https://raw.githubusercontent.com/openai/whisper/main/README.md`
3. 生成分析摘要
4. 写入飞书表格
5. 返回结果

**返回格式：**
~~~
### 📦 openai/whisper

**核心功能：** OpenAI 开源的语音识别模型，支持多语言转录和翻译。

**使用场景：**
- 视频字幕自动生成
- 会议记录转录
- 多语言内容翻译

**快速开始：**
```bash
pip install openai-whisper
whisper audio.mp3 --model base --language Chinese
```

**技术栈：** Python, PyTorch, AI/ML

**推荐指数：** 高（文档完善，实用性强）

---
✅ 已保存到 [GitHub Repo 收藏表](https://magictavern.feishu.cn/base/UU99brPBfa7ECrsOjgqc2XZDnXf)
~~~

## 注意事项

1. **保持分析简洁**：目标是快速筛选，不是深度解读
2. **突出实用性**：重点说明"能用来干什么"，而非技术细节
3. **原文链接必带**：方便用户快速跳转查看
4. **飞书表格是主存储**：分析结果必须写入表格，便于后续追踪
