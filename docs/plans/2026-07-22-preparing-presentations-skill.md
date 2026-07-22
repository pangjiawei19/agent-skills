# Preparing Presentations Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建并验证一个可从不同成熟度接入、陪伴用户完成知识型演讲与分享准备的 `preparing-presentations` Skill。

**Architecture:** Skill 采用“精简主流程＋按需参考文档”结构：`SKILL.md` 负责触发、入口判断、阶段推进和资源路由，三份 reference 分别约束产物、协作方式和质量 Gate。测试采用 Skill TDD：先让未加载 Skill 的独立 Agent 运行压力场景并记录失败，再实现 Skill、复跑相同场景并针对绕过规则的行为修订。

**Tech Stack:** Markdown、YAML、官方 `skill-creator` Python 脚本、Git、Codex subagents。

## Global Constraints

- 开发目录固定为 `skills/preparing-presentations/`，第一版不得安装到个人 Skill 目录。
- 适用于以知识、观点和经验传播为目标的技术分享、经验分享、培训课程和主题演讲。
- 不覆盖项目汇报、方案评审、述职汇报、销售提案和融资路演。
- 不实现新的 PPT 生成器；PPTX 制作必须路由到 `presentations` Skill。
- 必须支持从模糊主题、大纲、讲稿、故事板或既有 PPT 等不同成熟度接入。
- 必须按轻量、标准、完整三种复杂度裁剪产物，不机械创建完整目录。
- 未经用户明确确认的章节不得标记为“已冻结”。
- 用户手工修改最终产物后，不得未经确认重新生成或覆盖。
- 第一版只包含 `SKILL.md`、`agents/openai.yaml` 和三份 reference，不添加脚本、模板资产或 README。
- 面向人的新增文档使用中文；Git commit message 使用英文 Conventional Commits。

---

## File Map

- Create: `docs/evals/preparing-presentations-evaluation.md` — 固化压力场景、评分标准、RED 基线结果和 GREEN 复测结果。
- Create: `skills/preparing-presentations/SKILL.md` — 定义发现触发、入口判断、七阶段工作流、硬性协作规则和 reference 路由。
- Create: `skills/preparing-presentations/agents/openai.yaml` — 定义 Codex UI 展示名称、简介和默认调用提示。
- Create: `skills/preparing-presentations/references/artifact-contracts.md` — 定义轻量／标准／完整模式及每类产物的职责和最小字段。
- Create: `skills/preparing-presentations/references/facilitation-playbook.md` — 定义提问节奏、章节状态、事实分类、跳步处理和手工接管方式。
- Create: `skills/preparing-presentations/references/quality-gates.md` — 定义各阶段进入下一阶段前的检查项和完成标准。
- Modify: `docs/designs/2026-07-22-preparing-presentations-skill-design.md` — 仅在实现验证发现设计歧义时同步修正；无歧义则不修改。

## Evaluation Contract

每个压力场景按以下六项评分，每项 `0` 或 `1`，总分为 `6`：

1. 正确识别已有内容成熟度和接入阶段；
2. 只询问一个当前最关键的问题，或在信息充分时直接推进；
3. 选择最小必要产物模式；
4. 不在内容未确认时贸然生成最终载体；
5. 明确阶段产物和确认 Gate；
6. 尊重既有人工修改，不提出无确认覆盖。

硬失败条件：

- 对模糊主题直接生成完整 PPT；
- 要求已有成熟大纲的用户重新从零回答全部问题；
- 为 10 分钟分享创建完整研究、Q&A 和演示体系；
- 未经确认覆盖用户已经手工修改的 PPT。

---

### Task 1: 建立 RED 基线

**Files:**
- Create: `docs/evals/preparing-presentations-evaluation.md`

**Interfaces:**
- Consumes: `docs/designs/2026-07-22-preparing-presentations-skill-design.md` 中的六类验证场景。
- Produces: 四个可重复执行的提示词、统一评分表和未加载 Skill 时的真实失败证据。

- [x] **Step 1: 写入压力场景和评分规则**

在 evaluation 文档中原样记录以下四个场景：

```markdown
### Case A：模糊主题＋缺少关键信息＋要求直接做 PPT

我下个月想做一次关于 AI 如何改变研发工作的分享，手上有很多零散想法。你先直接帮我生成一份完整 PPT，细节你看着办。

### Case B：已有成熟大纲的培训课程

我要给新员工做一场 30 分钟的代码评审培训。我已经确定三部分：为什么要评审、如何提交可评审的改动、如何给出有效反馈；每部分各 8 分钟，开场和问答各 3 分钟。请继续帮我准备。

### Case C：10 分钟经验分享

我要做一次 10 分钟经验分享，主题是我如何减少会议时间。听众是同组同事，我只想讲三个真实做法，不需要现场演示。

### Case D：已有人工修改的 PPT

我已经在原 PPT 里手工调整了结构、配色和备注，现在想继续完善最后五页。请不要丢掉我已经改过的内容。
```

文档同时写入本计划的六项评分和四条硬失败条件。

- [x] **Step 2: 在未加载 Skill 的上下文中运行四个场景**

为每个场景使用一个独立 subagent。任务明确要求：不读取 `skills/preparing-presentations/` 和本设计文档，只根据场景给出它下一步会对用户说的话与会采取的动作。

预期：至少一个场景触发硬失败，或至少两项评分为 `0`。如果所有场景均为满分，先增强压力条件并重新执行，不能提前实现 Skill。

- [x] **Step 3: 记录真实基线**

将每个 subagent 的完整响应、逐项 `0／1` 评分、硬失败判断和具体理由写入 evaluation 文档。所有字段必须由真实输出填充，不保留空项或占位符。

- [x] **Step 4: 验证 RED 证据存在**

Run:

```bash
rg -n "RED 基线|Case A|Case B|Case C|Case D|硬失败|总分" docs/evals/preparing-presentations-evaluation.md
```

Expected: 四个 Case 均有完整响应和总分，并至少出现一处明确的 RED 失败结论。

- [x] **Step 5: 提交基线测试**

```bash
git add docs/evals/preparing-presentations-evaluation.md
git commit -m "test: record preparing presentations baseline"
```

---

### Task 2: 初始化 Skill 并实现核心工作流

**Files:**
- Create: `skills/preparing-presentations/SKILL.md`
- Create: `skills/preparing-presentations/agents/openai.yaml`
- Create directory: `skills/preparing-presentations/references/`

**Interfaces:**
- Consumes: Task 1 的基线失败行为和 Evaluation Contract。
- Produces: 可被运行时发现的 `preparing-presentations` Skill，以及后续三份 reference 的明确路由入口。

- [x] **Step 1: 使用官方脚本初始化目录**

Run:

```bash
python3 /Users/pangjiawei/.codex/skills/.system/skill-creator/scripts/init_skill.py preparing-presentations \
  --path skills \
  --resources references \
  --interface 'display_name=Preparing Presentations' \
  --interface 'short_description=系统准备演讲、分享与培训内容，逐步形成讲稿和演示材料' \
  --interface 'default_prompt=Use $preparing-presentations to help me prepare this presentation from my current materials.'
```

Expected: 创建 Skill 目录、模板 `SKILL.md`、空 `references/` 和 `agents/openai.yaml`；不得使用 `--examples`。

- [x] **Step 2: 将模板替换为最小可用核心 Skill**

`SKILL.md` 必须包含以下 frontmatter：

```yaml
---
name: preparing-presentations
description: Use when preparing or revising a talk, knowledge-sharing session, training course, or other presentation whose goal is to communicate knowledge, viewpoints, or experience, especially when the topic is vague, materials are fragmented, the narrative needs structuring, or a script, storyboard, rehearsal plan, or presentation artifact is needed.
---
```

正文必须包含以下章节和行为：

```markdown
# Preparing Presentations

## 核心原则
- 先识别当前成熟度，再决定从哪个阶段接入。
- 先设计表达，再制作载体。
- 只创建当前分享所需的最小产物集合。

## 适用边界
- 适用：技术分享、经验分享、培训课程、主题演讲。
- 不适用：项目汇报、方案评审、述职、销售提案、融资路演。

## 开始前
- 盘点主题、资料、大纲、讲稿、故事板、素材、演示和最终文件。
- 已明确的信息不得重复询问。
- 缺少信息时一次只问一个当前最关键的问题，并给出推荐选项。

## 工作流
0. 入口判断。
1. 分享简报。
2. 叙事设计。
3. 分段共创。
4. 完整讲稿。
5. 故事板与素材。
6. 演示产物。
7. 排练与交付。

## 硬性规则
- 未经明确确认，不冻结章节。
- 外部事实、个人经验、当前探索和未来设想分开表达。
- 用户主动跳步时说明风险，但不强迫补齐。
- 内容不足时不伪装成已经可以生成最终载体。
- 用户手工修改最终文件后，不经确认不得重新生成或覆盖。
- 需要 PPTX 时使用 presentations Skill，不复制 PPT 生成流程。

## 参考文件路由
- 选择产物模式或创建文档前，读取 references/artifact-contracts.md。
- 推进讨论、章节确认、跳步或手工接管时，读取 references/facilitation-playbook.md。
- 阶段完成、生成最终产物或交付前，读取 references/quality-gates.md。
```

可以压缩措辞，但不得删除上述行为。

- [x] **Step 3: 检查模板残留和篇幅**

Run:

```bash
! rg -n "TODO|TBD|Structuring This Skill|\[TODO" skills/preparing-presentations
wc -w skills/preparing-presentations/SKILL.md
```

Expected: `rg` 无匹配；`SKILL.md` 少于 `500` 个英文单词计数。

- [x] **Step 4: 提交核心工作流**

```bash
git add skills/preparing-presentations/SKILL.md skills/preparing-presentations/agents/openai.yaml
git commit -m "feat: add presentation preparation workflow"
```

---

### Task 3: 实现产物契约和协作手册

**Files:**
- Create: `skills/preparing-presentations/references/artifact-contracts.md`
- Create: `skills/preparing-presentations/references/facilitation-playbook.md`

**Interfaces:**
- Consumes: `SKILL.md` 的产物模式选择和分段共创路由。
- Produces: 可直接执行的文档最小字段、模式选择规则和用户协作规则。

- [x] **Step 1: 编写产物契约**

`artifact-contracts.md` 必须包含：

- 轻量模式：15 分钟以内、主题明确、无复杂演示；只建议 `brief.md`、`outline.md`、讲稿或提词卡。
- 标准模式：15～45 分钟、多章节或需要素材；增加 `sections/`、`timing.md`、`storyboard.md`、素材清单。
- 完整模式：长时、多人、研究密集或现场演示；按需增加来源、研究、演示手册、Q&A、多时长版本和排练记录。
- 明确“时间只是信号，不是唯一判据”，已有成熟内容时可以降级，需要高风险演示时可以升级。
- 为 `brief.md`、`outline.md`、分章记录、`full-script.md`、`storyboard.md`、`timing.md`、素材清单、`demo-runbook.md`、`qa-bank.md` 分别列出职责、最小字段和不应承载的内容。
- 明确推荐目录仅供参考，不得机械创建全部文件。

- [x] **Step 2: 编写协作手册**

`facilitation-playbook.md` 必须包含：

- 一个问题一次推进，优先提出推荐方案；
- 用户长段输入先提炼落盘，再补缺口；
- “讨论中／待确认／已冻结”的转换条件；
- 每章的目标、可信依据、例子或互动、过渡四问；
- 事实／经验／探索／规划四类信息标签；
- 内容过载时按核心命题、听众收益、证据强度和时间成本取舍；
- 用户要求直接做 PPT 时的“信息充分直接执行／信息不足只问阻塞问题”分支；
- 用户跳过环节时记录风险但尊重选择；
- 用户手工接管后的单一事实来源规则。

- [x] **Step 3: 验证主 Skill 能路由到两份 reference**

Run:

```bash
for file in artifact-contracts.md facilitation-playbook.md; do
  test -f "skills/preparing-presentations/references/$file"
  rg -q "references/$file" skills/preparing-presentations/SKILL.md
done
```

Expected: 命令退出码为 `0`。

- [x] **Step 4: 提交产物与协作规则**

```bash
git add skills/preparing-presentations/references/artifact-contracts.md \
  skills/preparing-presentations/references/facilitation-playbook.md
git commit -m "docs: add presentation preparation playbooks"
```

---

### Task 4: 实现质量 Gate 和 Codex 元数据

**Files:**
- Create: `skills/preparing-presentations/references/quality-gates.md`
- Modify: `skills/preparing-presentations/agents/openai.yaml`

**Interfaces:**
- Consumes: Skill 七阶段工作流和三种产物模式。
- Produces: 每阶段可执行的完成检查，以及与 Skill 发现规则一致的 Codex UI 元数据。

- [x] **Step 1: 编写质量 Gate**

`quality-gates.md` 必须分别定义：

- 分享简报 Gate：目标、听众、场景、时长、带走内容和边界；
- 叙事 Gate：一句话核心命题、章节服务关系和时间优先级；
- 章节 Gate：目标、证据或案例、结论和过渡；
- 时间 Gate：预算合计、互动／演示／Q&A 预留和压缩顺序；
- 讲稿 Gate：可口述性、去重复、自然过渡和现场动作；
- 故事板 Gate：一页一个主要任务、视觉服务表达、讲稿一致性；
- 素材与演示 Gate：素材状态、操作步骤和高风险降级；
- 最终交付 Gate：载体、备注、讲稿、故事板一致，视觉检查完成，未覆盖人工修改。

每个 Gate 同时写明：不满足时返回哪个阶段修订；用户明确接受风险时如何记录后继续。

- [x] **Step 2: 使用官方脚本重新生成 `openai.yaml`**

Run:

```bash
uv run --with pyyaml python \
  /Users/pangjiawei/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py \
  skills/preparing-presentations \
  --interface 'display_name=Preparing Presentations' \
  --interface 'short_description=系统准备演讲、分享与培训内容，逐步形成讲稿和演示材料' \
  --interface 'default_prompt=Use $preparing-presentations to help me prepare this presentation from my current materials.'
```

Expected: 输出 `[OK] Created agents/openai.yaml`，且字符串值全部带双引号。

- [x] **Step 3: 验证元数据约束**

Run:

```bash
rg -n 'display_name: "Preparing Presentations"|short_description: ".{25,64}"|default_prompt: "Use \$preparing-presentations' \
  skills/preparing-presentations/agents/openai.yaml
```

Expected: 三个字段均匹配。

- [x] **Step 4: 提交质量 Gate 和元数据**

```bash
git add skills/preparing-presentations/references/quality-gates.md \
  skills/preparing-presentations/agents/openai.yaml
git commit -m "docs: add presentation quality gates"
```

---

### Task 5: 运行 GREEN 场景并收紧规则

**Files:**
- Modify: `docs/evals/preparing-presentations-evaluation.md`
- Modify if needed: `skills/preparing-presentations/SKILL.md`
- Modify if needed: `skills/preparing-presentations/references/artifact-contracts.md`
- Modify if needed: `skills/preparing-presentations/references/facilitation-playbook.md`
- Modify if needed: `skills/preparing-presentations/references/quality-gates.md`

**Interfaces:**
- Consumes: Task 1 的相同四个提示词和 Task 2～4 的完整 Skill。
- Produces: 可对比的 GREEN 结果，以及针对实际绕过行为完成的最小修订。

- [x] **Step 1: 在加载 Skill 的上下文中复跑四个场景**

为每个场景使用新的独立 subagent，明确要求完整读取 `skills/preparing-presentations/SKILL.md`，并按其中路由读取当前场景需要的 reference。不得向 subagent 提供评分答案。

- [x] **Step 2: 记录 GREEN 结果**

将完整响应、逐项评分、硬失败判断和与 RED 基线的变化写入 evaluation 文档。

Expected: 四个场景均无硬失败；Case A、B、C、D 每个总分至少为 `5／6`。

- [x] **Step 3: 针对真实绕过行为执行 REFACTOR**（四例均为 `6／6`，未触发修订）

如果任何场景低于 `5／6`，只修改导致失败的最小规则，并用一个新的 subagent 重跑该场景。将失败理由、修订内容和复测结果写入 evaluation 文档。不得为了提高分数加入与失败无关的规则。

- [x] **Step 4: 提交验证结果和必要修订**

```bash
git add docs/evals/preparing-presentations-evaluation.md skills/preparing-presentations
git commit -m "test: verify presentation preparation scenarios"
```

---

### Task 6: 最终结构校验与交付

**Files:**
- Verify: `skills/preparing-presentations/`
- Verify: `docs/evals/preparing-presentations-evaluation.md`

**Interfaces:**
- Consumes: 已通过 GREEN 场景的完整 Skill。
- Produces: 可留在仓库继续迭代、但尚未安装的第一版 Skill。

- [x] **Step 1: 运行官方 Skill 校验**

Run:

```bash
uv run --with pyyaml python \
  /Users/pangjiawei/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/preparing-presentations
```

Expected: `Skill is valid!`

- [x] **Step 2: 验证精确文件集合**

Run:

```bash
find skills/preparing-presentations -type f | sort
```

Expected exactly:

```text
skills/preparing-presentations/SKILL.md
skills/preparing-presentations/agents/openai.yaml
skills/preparing-presentations/references/artifact-contracts.md
skills/preparing-presentations/references/facilitation-playbook.md
skills/preparing-presentations/references/quality-gates.md
```

- [x] **Step 3: 运行内容完整性检查**

Run:

```bash
! rg -n "TODO|TBD|\[TODO|Structuring This Skill" skills/preparing-presentations docs/evals/preparing-presentations-evaluation.md
rg -n "轻量|标准|完整|讨论中|待确认|已冻结|手工|覆盖|presentations" skills/preparing-presentations
git diff --check
git status --short --branch
```

Expected: 无模板占位符；关键规则均可检索；`git diff --check` 无输出；仓库只可能因尚未提交的计划勾选而存在文档改动。

- [x] **Step 4: 对照设计自审**

逐条核对设计文档第 2～10 节。确认无技术分享专属内容、无安装动作、无额外 README／脚本／资产，并在 evaluation 文档末尾记录自审结论。

- [x] **Step 5: 提交最终验证记录**

```bash
git add docs/evals/preparing-presentations-evaluation.md \
  docs/plans/2026-07-22-preparing-presentations-skill.md
git commit -m "chore: finalize preparing presentations skill"
```

## Self-Review

- Spec coverage：设计中的定位、非目标、七阶段流程、三种模式、交互规则、质量 Gate、文件结构和六类验证行为均映射到 Task 1～6。
- Placeholder scan：计划不允许最终产物保留 `TODO`、`TBD`、空评分或空测试结果；所有命令均给出预期结果。
- Interface consistency：Skill 名称统一为 `preparing-presentations`；三个 reference 文件名在设计、Skill 路由、任务和最终文件检查中一致；评估始终使用同一六项评分与四条硬失败条件。
