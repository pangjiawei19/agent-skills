# 自进化闭环模板

这些模板用于给目标 Skill 记录运行轨迹、生成阶段复盘，并在修改后做回归检查。使用时把 `<skill-name>` 替换为目标 Skill 名称，把检查项调整为目标 Skill 的真实流程。

## 数据目录

项目 Skill：

```text
<project-root>/skill-self-evolution/skill-runs/<skill-name>/
<project-root>/skill-self-evolution/skill-reviews/<skill-name>/
```

全局 Skill：

```text
~/.agents/skill-self-evolution/skill-runs/<skill-name>/
~/.agents/skill-self-evolution/skill-reviews/<skill-name>/
```

## 运行轨迹文件命名

```text
skill-self-evolution/skill-runs/<skill-name>/YYYY-MM-DD-<run-title>.md
```

全局 Skill 使用：

```text
~/.agents/skill-self-evolution/skill-runs/<skill-name>/YYYY-MM-DD-<run-title>.md
```

`<run-title>` 是本次运行任务的短标题，用于让人一眼知道这条轨迹记录的是哪次使用。命名规则：

- 有明确目标对象时，用对象名，例如文章标题、文档标题、任务名、会议名、发布单号。
- 没有明确目标对象时，用用户意图摘要，例如 `创建-周报模板`、`查询-待办任务`、`复盘-K8s-发布失败`。
- 失败或中断也照样记录，必要时加状态，例如 `抓取-公众号文章-失败`。
- 安全化文件名：去掉 `/ \ : * ? " < > |`；空格转 `-`；过长时截断到约 ３０～５０ 字。
- 同一天同名冲突时，在末尾加序号，例如 `生成-产品需求文档-2.md`。

示例：

```text
skill-self-evolution/skill-runs/tech-article-workbench/2026-07-06-《如何更科学、方向可控的实现-Skill-的自进化》.md
skill-self-evolution/skill-runs/lark-mail/2026-07-06-处理-张三-日报邮件.md
skill-self-evolution/skill-runs/release-orchestrator/2026-07-06-复盘-K8s-发布失败.md
```

## 运行轨迹模板

```markdown
---
skill: <skill-name>
skill_version:
日期:
用户意图:
输入摘要:
关联产物:
结果: 完成 / 部分完成 / 失败
触发复盘: 否 / 数量触发 / 同类问题 / 高风险问题
---

# 运行摘要

## 输入与目标

用户这次要目标 Skill 做什么，目标 Skill 实际识别出的任务是什么。

## 执行路径

- 触发了哪些主流程步骤
- 读取或写入了哪些关键文件
- 调用了哪些关键工具或外部系统
- 用户是否中途纠正方向

## 质量检查

| 项目 | 状态 | 说明 |
| --- | --- | --- |
| 意图识别 | 通过 / 问题 / 不适用 |  |
| 输入处理 | 通过 / 问题 / 不适用 |  |
| 核心流程 | 通过 / 问题 / 不适用 |  |
| 产物质量 | 通过 / 问题 / 不适用 |  |
| 状态更新 | 通过 / 问题 / 不适用 |  |
| 风险控制 | 通过 / 问题 / 不适用 |  |

## 问题与观察

记录具体问题、摩擦点、用户纠正、执行者自己的判断。区分偶发失误、流程缺口、模板缺口和高风险问题。

## 候选改动

只记录可能要改 Skill 的想法，不直接执行。每条标注：

- 类型：新增规则 / 修改流程 / 模板调整 / 工具策略 / 验证保护
- 证据：单次观察 / 重复出现 / 高风险 / 用户明确要求
- 建议：暂存观察 / 进入复盘 / 立即加保护

## 下次注意

给下一次使用目标 Skill 的短提醒。
```

## 阶段复盘文件命名

目录已经包含 `<skill-name>`，复盘文件名默认不再重复写 skill name：

```text
skill-self-evolution/skill-reviews/<skill-name>/YYYY-MM-DD-review.md
```

全局 Skill 使用：

```text
~/.agents/skill-self-evolution/skill-reviews/<skill-name>/YYYY-MM-DD-review.md
```

同一天多次复盘时，只用序号解决冲突，不在文件名里加入复盘范围或问题类型。复盘范围写在文件正文的「覆盖范围」里。

```text
skill-self-evolution/skill-reviews/<skill-name>/YYYY-MM-DD-review-2.md
skill-self-evolution/skill-reviews/<skill-name>/YYYY-MM-DD-review-3.md
```

## 阶段复盘模板

```markdown
# <skill-name> 阶段复盘

当前版本：

## 覆盖范围

本次复盘查看了哪些运行轨迹。

## 质量概览

按运行轨迹中的质量检查项汇总表现。

## 重复问题

哪些问题出现了 ２ 次以上，证据分别来自哪几次运行。

## 高风险问题

是否出现需要立即加保护的情况，例如误删、覆盖、污染数据、错误发布、错误修改 Skill。

## 候选改动

每条候选改动包含：

- 问题
- 证据
- 建议改动位置
- 预期收益
- 潜在风险
- 建议版本变化
- 是否建议本轮执行

## 不采纳项

记录哪些观察暂时不改 Skill，以及为什么不改。

## 回归检查建议

如果要改 Skill，改完后至少检查哪些路径。
```

## 通用回归检查清单

每次修改目标 Skill 后，至少检查：

| 路径 | 检查点 |
| --- | --- |
| 触发 | description 是否仍能准确触发目标场景 |
| 路由 | 用户主要意图是否仍能走到正确流程 |
| 输入 | 常见输入、缺失输入、歧义输入是否有处理规则 |
| 主流程 | 核心步骤是否保持顺序和停顿点 |
| 输出 | 产物格式、命名、链接、状态更新是否正确 |
| 风险 | 删除、覆盖、发布、发消息、改 Skill 等高风险动作是否有确认 |
| 记录 | 运行轨迹是否仍会写入正确目录 |
| 复盘 | 候选改动是否仍只记录，未绕过用户确认 |
```
