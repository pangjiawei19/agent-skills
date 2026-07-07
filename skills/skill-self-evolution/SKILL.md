---
name: skill-self-evolution
version: 0.1.1
description: 给 Skill 加装和运营自进化闭环。Use when the user asks to add self-evolution, run logging, review cycles, improvement evidence, candidate changes, regression gates, or controlled iteration to an existing skill; when adapting the mechanism from one skill to another; or when reviewing a skill's run traces to decide whether and how to update the skill.
---

# Skill Self Evolution

给目标 Skill 加装一套轻量、自控、可复盘的自进化机制。核心闭环是：

`运行轨迹 → 阶段复盘 → 候选改动 → 用户确认 → 小步修改 → 回归检查`

## 核心原则

- 不根据单次运行直接修改目标 Skill。
- 候选改动默认只记录，不自动执行。
- 同类问题出现 ２ 次以上，或出现高风险问题，才建议进入复盘。
- 单次修改最多落地 １～３ 条规则。
- 优先修改局部流程、模板或保护规则，避免重写整个 `SKILL.md`。
- 修改前说明证据、改动位置、预期收益和潜在风险，并等待用户确认。
- 修改后按目标 Skill 的回归检查清单验证。
- 运行结束写轨迹前，默认向用户轻问一句使用感受或改进想法；用户不回答则跳过，不影响收尾。

## 版本管理

- 支持在目标 Skill 的 `SKILL.md` frontmatter 顶层维护 `version` 字段，例如 `version: 0.1.0`。
- `version` 表示当前 Skill 规则版本；精确变更历史仍以 git commit 和阶段复盘文件为准。
- 只有用户明确要求启用版本管理，或目标 Skill 已经存在 `version` 字段时，才维护该字段。
- 修改目标 Skill 后，如果本轮改动改变了规则、流程、模板或保护边界，应在用户确认的修改范围内同步更新 `version`。
- 默认采用语义化版本：破坏性或大范围流程调整升主版本；新增能力升次版本；文案、模板细节、局部保护规则升补丁版本。

## 工作流

### １．识别目标 Skill

先定位目标 Skill 的根目录和归属：

- 项目 Skill：通常位于 `<project-root>/.agents/skills/<skill-name>/`。
- 全局 Skill：通常位于 `~/.agents/skills/<skill-name>/`。
- 其他位置：按用户给出的路径处理，并明确说明数据目录将放在哪里。

如果目标不明确，先请用户给出 Skill 名称或路径。

### ２．选择数据目录

默认采用“数据跟 Skill 归属走”：

- 项目 Skill：
  - `<project-root>/skill-self-evolution/skill-runs/<skill-name>/`
  - `<project-root>/skill-self-evolution/skill-reviews/<skill-name>/`
- 全局 Skill：
  - `~/.agents/skill-self-evolution/skill-runs/<skill-name>/`
  - `~/.agents/skill-self-evolution/skill-reviews/<skill-name>/`

用户明确指定时，可以覆盖默认路径。

### ３．加装机制

当用户要求给目标 Skill 加装自进化机制时：

1. 读取目标 `SKILL.md` 和必要 reference 文件，理解目标 Skill 的主流程、输出物和高风险操作。
2. 读取 `references/install-guide.md`。
3. 给出加装方案，说明将新增哪些目录、模板、流程步骤和边界规则。
4. 等用户确认后，再修改目标 Skill。
5. 修改后按 `references/templates.md` 中的回归检查结构做验证。

不要在未确认方案时直接改目标 Skill。

### ４．记录运行轨迹

当一次目标 Skill 使用结束后，按 `references/templates.md` 的运行轨迹模板记录：

- 用户意图与目标；
- 执行路径；
- 质量检查；
- 用户反馈；
- 问题与观察；
- 候选改动；
- 下次注意。

写入运行轨迹前，先用一句轻量问题询问用户是否有使用感受、改进想法、偏好或下次期望需要记录。用户反馈只进入运行轨迹和候选改动，不直接修改目标 Skill，也不绕过阶段复盘和用户确认。

只写结构化复盘，不保存完整对话转录。

### ５．阶段复盘

当满足任一条件时，按 `references/review-guide.md` 生成阶段复盘：

- 累计 ５ 次新的运行轨迹；
- 同一类问题出现 ２ 次；
- 出现高风险问题，例如误删、覆盖、污染数据、错误发布、错误修改 Skill。

复盘报告只归纳证据并提出候选改动；是否修改目标 Skill 由用户确认。

## 资源

- `references/templates.md`：运行轨迹、阶段复盘和回归检查模板。
- `references/install-guide.md`：给目标 Skill 加装自进化机制的步骤。
- `references/review-guide.md`：从运行轨迹做阶段复盘和候选改动判断的方法。
