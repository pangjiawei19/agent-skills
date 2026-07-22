# Preparing Presentations Narrative Cohesion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强 `preparing-presentations` 对章节闭环、相邻页面过渡和结尾全场回顾的约束。

**Architecture:** 在现有四个 Skill 文档中做最小增量修改，不改变第一版自适应入口和产物模式。先用 Case E～G 记录当前 Skill 的真实失败，再补充产物字段、协作检查和质量 Gate，最后复跑相同场景并检查 Case A～D 的关键规则未回退。

**Tech Stack:** Markdown、YAML、官方 `skill-creator` 校验脚本、Git、Codex subagents。

## Global Constraints

- 不为轻量分享强制增加章节幕封或总结页。
- 标准和完整模式默认规划章节幕封，也允许清晰的口头定位替代新增页面。
- 章节必须形成“问题 → 内容与证据 → 结论 → 下一章桥接”。
- 页面过渡必须能落入讲稿，不接受只有抽象的“与前后页相关”。
- 结尾回顾必须包含全场路线、核心结论和听众下一步行动，不机械重放目录。
- 不修改 PPT 视觉生成实现。
- 不改变现有 Skill 的自适应入口、产物裁剪、用户跳步和手工接管规则。

---

### Task 1: 建立叙事连贯性 RED 基线

**Files:**
- Modify: `docs/evals/preparing-presentations-evaluation.md`

**Interfaces:**
- Consumes: 当前未修改的 `skills/preparing-presentations/`。
- Produces: Case E～G 的原始响应、六项评分和明确失败证据。

- [ ] **Step 1: 写入新增评分规则和场景**

评分项：章节开场定位、章节总结与桥接、幕封或口头等价物、相邻页面可口述过渡、结尾路线回顾与行动、避免机械增加页面。硬失败分别为：接受无章节边界、只笼统建议加强衔接、接受 Q&A-only 结尾。

- [ ] **Step 2: 使用独立 subagent 运行 Case E～G**

测试 Agent 读取当前 Skill 和所需 reference，但不得看到增量设计、评分规则或期望答案。三个场景使用设计文档第 7 节的输入，要求返回直接回复用户的内容和随后动作。

- [ ] **Step 3: 记录并验证 RED**

完整记录响应、逐项评分和失败理由。至少一个场景触发硬失败或总分低于 `5／6`，否则增强压力条件后重跑。

- [ ] **Step 4: 提交 RED 基线**

```bash
git add docs/evals/preparing-presentations-evaluation.md \
  docs/plans/2026-07-22-preparing-presentations-narrative-cohesion.md
git commit -m "test: record narrative cohesion baseline"
```

---

### Task 2: 实现章节闭环和逐页连接

**Files:**
- Modify: `skills/preparing-presentations/SKILL.md`
- Modify: `skills/preparing-presentations/references/artifact-contracts.md`
- Modify: `skills/preparing-presentations/references/facilitation-playbook.md`
- Modify: `skills/preparing-presentations/references/quality-gates.md`

**Interfaces:**
- Consumes: Task 1 暴露的实际失败。
- Produces: 可执行的章节闭环、相邻页串读和结尾回顾规则。

- [ ] **Step 1: 更新主 Skill**

在硬性规则中加入：标准和完整模式需要清晰章节边界；每章有问题、结论和下一章桥接；故事板与讲稿需要可口述页面过渡；Q&A 前完成全场路线回顾、核心结论和行动。

- [ ] **Step 2: 更新产物契约**

为大纲和分章记录增加章节问题、结论、回顾、桥接和幕封决策；为故事板增加承接上一页、本页角色、引出下一页和过渡句；为讲稿和结尾增加设计文档第 4 节的字段。

- [ ] **Step 3: 更新协作手册**

增加章节回顾与“下一章为什么此时出现”的确认；增加相邻页串读、骨架串读及七类常见页面关系；明确过渡不能模板化。

- [ ] **Step 4: 更新质量 Gate**

增加章节边界、页面连接和结尾回顾三个 Gate，并写清失败时返回的阶段。

- [ ] **Step 5: 提交最小实现**

```bash
git add skills/preparing-presentations
git commit -m "feat: strengthen presentation narrative cohesion"
```

---

### Task 3: GREEN 复测与回归检查

**Files:**
- Modify: `docs/evals/preparing-presentations-evaluation.md`
- Modify if needed: `skills/preparing-presentations/SKILL.md`
- Modify if needed: `skills/preparing-presentations/references/*.md`

**Interfaces:**
- Consumes: 与 Task 1 完全相同的 Case E～G。
- Produces: GREEN 对比、必要的最小 REFACTOR 和 Case A～D 不回退的证据。

- [ ] **Step 1: 使用新的独立 subagent 复跑 Case E～G**

每例至少 `5／6`，且不得触发硬失败。测试 Agent不得获得评分规则和期望答案。

- [ ] **Step 2: 针对真实绕过行为 REFACTOR**

只修改导致低分的最小规则，并重跑失败场景；没有失败则记录无需修订。

- [ ] **Step 3: 检查 Case A～D 关键规则**

静态核对以下行为仍存在：一次一个关键问题、轻量模式不膨胀、确认后冻结、人工修改文件不覆盖、PPTX 路由到 `presentations` Skill。

- [ ] **Step 4: 提交 GREEN 结果**

```bash
git add docs/evals/preparing-presentations-evaluation.md skills/preparing-presentations
git commit -m "test: verify narrative cohesion scenarios"
```

---

### Task 4: 最终验证

**Files:**
- Verify: `skills/preparing-presentations/`
- Verify: `docs/evals/preparing-presentations-evaluation.md`

**Interfaces:**
- Consumes: 已通过新增和原有规则检查的 Skill。
- Produces: 可继续留在功能分支的叙事连贯性增强版本。

- [ ] **Step 1: 运行官方校验**

```bash
uv run --with pyyaml python \
  /Users/pangjiawei/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/preparing-presentations
```

Expected: `Skill is valid!`

- [ ] **Step 2: 运行内容检查**

```bash
! rg -n "TODO|TBD|\[TODO|Structuring This Skill" skills/preparing-presentations
rg -n "章节幕封|章节边界|承接上一页|引出下一页|过渡句|相邻页串读|骨架串读|全场路线|下一步行动" skills/preparing-presentations
git diff --check
```

Expected: 无占位符和格式错误，新增规则均可检索。

- [ ] **Step 3: 提交最终验证状态**

```bash
git add docs/plans/2026-07-22-preparing-presentations-narrative-cohesion.md
git commit -m "chore: finalize narrative cohesion improvements"
```

## Self-Review

- Spec coverage：章节闭环、幕封或口头替代、逐页过渡、相邻页串读、骨架串读、结尾回顾和三个回归场景均有对应任务。
- Placeholder scan：计划没有未定义实现项；所有最终检查给出精确命令和预期结果。
- Interface consistency：增量测试统一使用 Case E～G；四个 Skill 文件和 evaluation 路径在设计与计划中一致。
