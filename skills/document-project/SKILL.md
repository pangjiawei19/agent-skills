---
name: document-project
description: Analyze existing codebase and generate comprehensive project documentation including overview, domain models, business flows, architecture, and dependencies. Use when the user asks to document a project, create project documentation, analyze codebase structure, or mentions terms like "项目文档", "整理文档", "项目说明", "代码分析", "架构梳理", "onboarding 文档".
---

# Project Documentation Generator

从现有代码库自动生成全面的项目文档，包括项目简介、核心领域模型、业务流程、项目结构和外部依赖。

## 工具兼容性

本 skill 使用 **Claude Code** 工具名（`Glob`、`Grep`、`Read`、`Bash`、`Agent` 等）。在其他 Agent 平台运行时，请将工具名理解为**操作意图**，替换为等价能力：

- **按文件名模式查找** → Glob / file_search 等
- **按内容正则搜索** → Grep / ripgrep 等
- **读取文件** → Read / read_file 等
- **执行 shell 命令** → Bash / shell 等
- **派发并行子任务** → Agent / subagent 等

完整映射见 [references/tool-mapping.md](references/tool-mapping.md)。

## 配套参考文件

- [references/tool-mapping.md](references/tool-mapping.md) — 跨平台工具映射表
- [references/language-hints.md](references/language-hints.md) — 按语言/框架的定位提示（Java/Node/Python/Go/Rust/Monorepo）
- [references/output-templates.md](references/output-templates.md) — 各 Step 的 markdown 输出样板
- [example-output.md](example-output.md) — 完整文档示例（虚构项目，仅示意结构）

**加载策略**（按需加载，不要一次全读）：
- `language-hints.md`：Step 1 识别项目类型后加载对应语言的小节，Step 2 / 3 / 5 复用
- `output-templates.md`：Step 1 / 2 / 3 / 4 / 5 各自产出前加载对应小节；Step 6 组装时加载 Step 6 骨架
- `tool-mapping.md`：仅在非 Claude Code 平台运行时需要加载

## 不适用场景（先判断）

如果目标仓库属于以下情况之一，本 skill **不适用**——应直接告知用户，而不是硬生成一份空洞文档：

- **纯文档仓库**（如博客、知识库，源代码 < 20 个非配置文件）
- **教学示例仓库**（README 明确标明 tutorial / example / demo / starter / template / boilerplate）
- **配置仓库**（仅含 YAML / JSON / Terraform / k8s manifests，无业务代码）
- **玩具项目**（单 main 文件 + < 5 个源文件 — 直接写 README 更合适）
- **空仓库或仅有构建骨架**（无业务代码）

**判断方式**：先用 Glob 统计非依赖源文件数量，再读 README 前 50 行判断仓库性质。

如命中以上情况，输出：
> 当前仓库看起来是 [类型]，不适合生成项目文档。建议改为：[根据类型给建议，如"补充 README"/"写单页说明"]。如仍需生成，请告知。

等用户确认后再继续；否则跳过本 skill。

---

## 输出路径规范（固定）

本 skill 始终生成到 **`docs/project-overview/`** 目录，采用一章一文件的拆分结构：

```
docs/project-overview/
├── README.md              # 入口：DOC_META 锚点 + 项目简介 + 总览目录
├── domain-model.md        # Step 2 输出
├── business-flows.md      # Step 3 输出
├── architecture.md        # Step 4 输出
├── dependencies.md        # Step 5 输出
├── deployment.md          # 部署说明（Step 6 一部分）
└── development.md         # 开发指南（Step 6 一部分）
```

- **DOC_META 锚点**固定写在 `README.md` 头部
- 不使用其他路径（不再支持 `docs/PROJECT_DOCUMENTATION.md` 或根目录 `DOCUMENTATION.md`）
- 一章一文件，增量更新时修改 `domain-model.md` 不影响其他章节，git diff 清晰

---

## Step 0: 前置检查（必须首先执行）

### 0.1 判断用户意图

用户显式要求**重新生成文档**时走**全量生成模式**，跳过下面的检查。触发词示例：
- 中文："重新生成"、"从头生成"、"重建文档"、"丢弃现有文档重新生成"
- 英文："regenerate"、"rebuild from scratch"、"rewrite"

⚠️ 注意："更新文档" / "update docs" 等表述**默认走增量**，不视为全量触发词。

### 0.2 检查 git 可用性

执行（stderr 重定向到 /dev/null 避免污染输出）：

```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

- **标准输出为 `true`** → 进入 0.3
- **命令失败、非零退出码、或 git 未安装** → 跳过变更检测，**强制走全量**，告知用户"项目非 git 仓库（或 git 不可用），将进行全量生成"；生成时 DOC_META 锚点的 `last_commit` 字段写 `none`

### 0.3 检查目标目录

使用 `Glob` 检查 `docs/project-overview/README.md` 是否存在：
- **不存在** → 走**全量生成模式**
- **存在** → 进入 0.4 提取锚点

### 0.4 提取上次生成的 commit 锚点

读取 `docs/project-overview/README.md` 头部的机器可读锚点（`last_commit` 固定 **12 位**短 hash）：

```markdown
<!-- DOC_META: last_commit=abc123def456, generated=2026-04-13 -->
```

- **找到锚点** → 进入 0.5 判断变更规模
- **未找到锚点**（旧文档未写入） → 提示用户"未找到版本锚点，建议全量重生成"；若用户坚持增量，尝试用 `git log -1 --format='%h' --abbrev=12 -- docs/project-overview/README.md` 推断基准 commit；该命令也返回空则**强制走全量**并告知用户

### 0.5 判断变更规模，决定模式

**判断顺序**（短路逻辑：命中即停，不继续向下判断）：

1. **先判断结构性变更** — 任一命中则提示用户"检测到结构性变更，建议全量重生成"
2. **再按变更文件占比判断** — 按下表决定模式

**结构性变更**信号（第 1 步使用，任一命中即视为结构性）：
- 构建文件变动（`pom.xml` / `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml`）
- 顶层目录新增或删除（如新增 `apps/`、`services/`）
- 主类 / 入口文件变动
- 数据库迁移文件新增

**变更文件占比**（第 2 步使用）：

```bash
# 分子：变更文件数
CHANGED=$(git diff <last_commit> HEAD --name-only | wc -l)

# 分母：源码文件总数（排除依赖、构建产物、lock 文件）
TOTAL=$(git ls-files | grep -Ev '(^|/)(node_modules|vendor|dist|build|target|\.lock|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|go\.sum)' | wc -l)

# 查看变更概览
git diff <last_commit> HEAD --stat
```

| 占比区间（CHANGED / TOTAL） | 模式 |
|----------------------------|------|
| `占比 < 10%` | **增量更新** |
| `10% ≤ 占比 ≤ 30%` | **增量更新**，但需重新扫描所有受影响章节 |
| `占比 > 30%` | 提示用户"变更规模较大，建议全量重生成" |

### 增量更新流程

1. **读取 `docs/project-overview/` 下相关文件**，保留未变更章节
2. **聚焦变更文件**：只对 `git diff <last_commit> HEAD --name-only` 返回的文件执行 Step 1-5 中的相关分析
3. **按「代码变更 → 文档文件」映射更新对应文件**：

   | 代码变更类型 | 更新的文档文件 |
   |-------------|--------------|
   | 实体类 / ORM schema | `domain-model.md` |
   | Controller / Handler / Service | `business-flows.md` |
   | 目录结构 / 模块划分 | `architecture.md` |
   | 构建文件 / 配置文件 | `dependencies.md` |
   | `Dockerfile` / CI / `Makefile` | `deployment.md` |
   | `CONTRIBUTING.md` / lint 配置 | `development.md` |
   | 构建文件中的项目元信息（名字、版本） | `README.md` |

4. **更新 `README.md` 头部锚点**：
   ```markdown
   <!-- DOC_META: last_commit=<HEAD commit 12 位>, generated=<今天日期> -->
   ```

### 全量生成流程

依次执行 Step 1-6，每步完成后用 TaskCreate/TaskUpdate 跟踪进度。

---

## Step 1: 项目概览分析

### 1.1 识别项目类型

检查构建文件确定项目类型：
- `pom.xml` / `build.gradle` → Java / Spring
- `package.json` → Node.js / 前端
- `requirements.txt` / `pyproject.toml` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust
- 顶层出现 `apps/` / `packages/` / `services/` / `pnpm-workspace.yaml` → Monorepo

识别后加载 [references/language-hints.md](references/language-hints.md) 查阅对应语言的详细提示。

### 1.2 收集基础信息（一次读完构建文件）

读取构建文件一次，**同时提取两类信息**（后续 Step 5 不再重读）：

- **项目元信息**（本步使用）：项目名称、版本、技术栈、构建工具、主要配置文件位置
- **完整依赖列表**（供 Step 5 使用）：所有 dependency 条目及其版本

在内部保存依赖列表，Step 5 直接引用而不是重新读构建文件。

### 1.3 扫描通用排查清单

优先读取：`README.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`Dockerfile`、`docker-compose.yml`、CI 配置（`.github/workflows/*`、`.gitlab-ci.yml`）、`Makefile`、`.env.example`、`openapi.yaml`。

输出格式见 [references/output-templates.md](references/output-templates.md) 的 Step 1 小节。

---

## Step 2: 领域模型提取

### 2.1 定位实体类

按项目类型选择查找策略，详见 [references/language-hints.md](references/language-hints.md) 的"实体定位"小节。

### 2.2 分析实体关系

识别主键/外键、一对多/多对多、继承、组合关系。优先使用框架注解（`@OneToMany`、`gorm` 标签、Prisma schema 等）作为事实来源。

### 2.3 筛选核心实体

大项目可能有 100+ 实体，全部详述会压垮 context 也无必要。按以下规则筛选**核心实体**：

**纳入核心实体的条件（满足任一）**：
- 被 ≥ 2 个 Service / Controller 直接操作（用 Grep 统计引用次数）
- 在代码中作为 `@OneToMany` / `@ManyToOne` / `@ManyToMany` 等关系的**主表或从表出现 ≥ 2 次**（从关系注解统计，不是从 ER 图反推）
- 是聚合根（DDD 项目）或 `@Entity` 标注为主表
- 字段数 ≥ 5（小的 join 表、枚举表一般不是核心）

**数量上限**：核心实体通常控制在 **10-15 个**。超出时：
- TOP 10-15 按上述格式详述
- 其余实体用精简表格附在末尾：`| 实体 | 用途 | 来源文件 |`

**筛选不到实体时**（如无 ORM 的项目）：转而分析主要数据结构（DTO、Value Object、Response 类型），标题改为"核心数据结构"。

### 2.4 记录核心实体

对每个**核心实体**记录：
- **实体名称和用途**（标注来源文件）
- **关键字段及含义**（仅列出代码中实际存在的字段）
- **业务规则**（⚠️ 只列出代码中可验证的规则，不要凭经验脑补）
- **关联关系**

**降级规则**：如果一个实体的核心字段（主键、外键、关键业务字段）都无法从代码确定，不要强行详述——降级到末尾的"次要实体表格"。

输出格式（含 Mermaid ER 图）见 [references/output-templates.md](references/output-templates.md) 的 Step 2 小节。

---

## Step 3: 业务流程梳理

### 3.1 识别业务入口

按项目类型定位，详见 [references/language-hints.md](references/language-hints.md) 的"业务入口"小节。

涵盖：REST API、GraphQL、消息队列消费、定时任务、事件处理、gRPC。

### 3.2 筛选主要业务流程

大项目可能有 50+ Controller 方法，全部画序列图不现实。按以下规则筛选：

**纳入主要流程的条件（满足任一）**：
- 围绕核心实体的**创建 / 状态变更**（如"创建订单"、"支付"、"审核通过"）
- 跨 ≥ 3 层调用（Controller → Service → Repository/External）
- 涉及**外部服务调用**（支付网关、MQ、邮件、第三方 API）
- 涉及**状态机**（订单状态、审批流等）
- 涉及**分布式锁 / 事务边界**

**数量上限**：主要流程通常控制在 **5-8 个**。超出时：
- TOP 5-8 画序列图 + 步骤说明
- 其余业务端点用精简表格罗列：`| 端点 | 方法 | 入口 Controller | 简述 |`

**追踪每个流程**：
1. 从入口点开始（Controller / Handler）
2. 追踪 Service 层调用（Grep 调用链）
3. 识别数据访问层（Repository / DAO / ORM）
4. 记录外部调用（第三方 API、消息队列）
5. 标注事务边界和异常处理

### 3.3 识别状态机

对核心实体（尤其是 `Order`、`Task`、`Workflow` 等）检查是否存在状态字段 + 状态转换逻辑：
- 枚举类（`OrderStatus.java`、`*State.java`）
- 状态机库（Spring Statemachine、`squirrel-foundation`、XState、自实现的 `switch-case`）
- 状态变更方法（`markAs*`、`transitionTo*`）

找到则画 `stateDiagram-v2`，标注来源文件。

### 3.4 绘制流程图

使用 Mermaid `sequenceDiagram` 或 `stateDiagram-v2`。

输出格式见 [references/output-templates.md](references/output-templates.md) 的 Step 3 小节。

---

## Step 4: 架构结构分析

### 4.1 扫描目录结构

使用 `Glob` 或等价工具扫描目录。**扫描深度按语言自适应**，目标是扫到能看到**关键业务目录**（`controller/`、`service/`、`entity/`、`handler/`、`router/` 等）为止：

| 语言 / 项目结构 | 推荐扫描深度 | 原因 |
|---------------|-------------|------|
| Java / Kotlin / Scala | 6-8 层 | 包路径嵌套深（`src/main/java/com/example/project/controller/`） |
| C# | 5-7 层 | namespace 路径嵌套 |
| Python / Node.js / Go / Rust | 3-5 层 | 路径通常较浅 |
| Monorepo | 先扫顶层 2 层定位子模块，再对每个子模块按上表深度扫描 | 避免一次性扫太多 |

**自适应策略**：如果按推荐深度还看不到业务关键词（controller/service/handler/router/model/entity），再加深 2 层；仍看不到则整体从 `src/` 或项目根起扫，忽略无关目录。

**忽略的目录**（所有语言通用）：`node_modules`、`target`、`build`、`dist`、`.git`、`vendor`、`__pycache__`、`.pytest_cache`、`.tox`、`.venv`、`*.egg-info`、`.next`、`.nuxt`、`.gradle`、`out`、`bin`、`obj`、`coverage`、`.idea`、`.vscode`。

> ⚠️ 不要把 `env/` 加入忽略列表——有些项目会把真实业务目录命名为 `env/`（环境相关配置或代码）。只忽略 `.venv/`、`.env/`（点开头）。

需要可视化目录树时可调用 `tree -L <深度> -I 'node_modules|target|build|dist'`（需确认环境已安装 `tree`，否则用 Glob 结果拼接）。

### 4.2 识别架构模式

从目录命名 + 包结构 + 关键注解推断：
- **分层架构**: Controller → Service → Repository
- **六边形架构**: Domain → Application → Infrastructure / Adapter
- **微服务架构**: 多个独立服务（顶层 `services/` 或 monorepo）
- **模块化单体**: 按业务域划分模块

### 4.3 分析代码组织

记录包/模块职责划分、公共组件、配置管理方式、测试代码组织。

输出格式见 [references/output-templates.md](references/output-templates.md) 的 Step 4 小节。

---

## Step 5: 依赖关系整理

### 5.1 使用 Step 1.2 已读取的依赖列表

直接使用 Step 1.2 中已提取的依赖列表，不要重新读构建文件。如果某些子模块（monorepo）的构建文件 Step 1 未扫描，再补读。

### 5.2 分类依赖（按实际情况取舍）

以下为**参考类别**，按项目实际取舍、可增删：

- **核心框架**（Web / RPC / ORM 框架等）
- **数据存储**（数据库、NoSQL）
- **缓存 / 消息队列**（Redis、Kafka、RabbitMQ 等）
- **工具库**
- **开发和测试**
- **项目特有类别**（如机器学习项目的"模型框架"、CLI 项目的"命令行解析"）

对于 **CLI 工具 / 纯库 / 纯前端**项目，"数据存储"、"消息队列"等类别可直接省略，避免空表格占位。

### 5.3 识别外部服务

从配置文件和代码查找：第三方 API、云服务（AWS / 阿里云等）、支付网关、短信/邮件服务。每项标注配置 key 前缀和调用文件位置。

输出格式（含依赖表格）见 [references/output-templates.md](references/output-templates.md) 的 Step 5 小节。

---

## Step 6: 生成完整文档

### 6.0 数据来源原则（⚠️ 必读，防止幻觉）

1. **只写从代码、配置、构建文件、README、CI 配置中可直接读出或合理推断的内容**。
2. **找不到来源 → 写 `待补充（需人工确认）`**，不要凭经验或示例脑补。
3. **模板中的具体值（如 `Java 11+`、`./gradlew build`）仅为格式示例，不是默认值**——必须替换为从当前项目读取到的实际值。
4. **重要断言标注来源**：如 `Java 17 (来源: pom.xml <java.version>)`、`启动命令（来源: Dockerfile CMD / README.md#运行）`。

### 6.1 可自动生成的章节 vs 需人工补充的章节

| 章节 | 数据来源 | 找不到来源时 |
|------|---------|------------|
| 项目简介 | 构建文件 + README | 从代码推断，标注 `[推断]` |
| 核心领域模型 | 实体类代码 + 注解 | **字段级**：略过无法确认的字段（保留实体骨架）；**实体级**：若核心字段（主键/外键/关键业务字段）都无法确定，降级到"次要实体"表格（见 Step 2.4 降级规则） |
| 业务流程 | Controller + Service 调用链 | 只画能追踪到的部分，标注 `[部分流程未覆盖]` |
| 项目结构 | 目录扫描 | 客观陈述，无需推断 |
| 外部依赖 | 构建文件 + 配置文件 | 无则不列 |
| **部署说明 - 环境要求** | 构建文件、`Dockerfile`、`docker-compose.yml`、CI 配置 | 未声明组件写 `待补充` |
| **部署说明 - 启动步骤** | `README`、`Makefile`、`package.json scripts`、`Dockerfile CMD`、CI workflow | 找不到则写 `待补充（未在代码库中发现启动脚本）` |
| **部署说明 - 配置说明** | `application-example.yml`、`.env.example`、配置类 | 不要编造配置项 |
| **开发指南** | `CONTRIBUTING.md`、`.editorconfig`、lint 配置、git hooks、`CODEOWNERS` | 找不到则整节写 `待补充（建议人工编写）` |

### 6.2 组装并拆分输出

按 [references/output-templates.md](references/output-templates.md) 的 Step 6 拆分骨架，将 Step 1-5 的产出 + 部署说明/开发指南**分别写入** `docs/project-overview/` 下的 7 个文件：

| 文件 | 内容 | 来自 |
|------|------|------|
| `README.md` | DOC_META 锚点 + 项目简介 + 总览目录（链接到其他章节） | Step 1 |
| `domain-model.md` | 核心领域模型、ER 图、实体详情、次要实体表格 | Step 2 |
| `business-flows.md` | 主要业务流程序列图 + 状态机 + 其他端点表格 | Step 3 |
| `architecture.md` | 架构模式、目录结构、模块说明 | Step 4 |
| `dependencies.md` | 依赖表格、第三方服务 | Step 5 |
| `deployment.md` | 环境要求、配置说明、启动步骤 | Step 6 |
| `development.md` | 本地开发、代码规范、提交规范、FAQ | Step 6 |

**`README.md` 头部必须写入机器可读锚点**（`last_commit` 固定 12 位 hash，非 git 仓库填 `none`）：

```markdown
<!-- DOC_META: last_commit=abc123def456, generated=2026-04-13 -->
```

**章节间互链**：各文件之间用相对链接跳转，如 `README.md` 目录项链接到 `./domain-model.md`；`business-flows.md` 提到某实体时链接到 `./domain-model.md#user-用户`。

### 6.3 先建目录再写入

写入前先创建目录：`mkdir -p docs/project-overview`（或等价的文件创建能力）。

### 6.4 生成摘要

给用户一段简短摘要：核心功能、主要技术栈、业务流程数量、核心实体数量、文档保存位置。

---

## Step 7: 输出质量自检（必做）

生成后按以下顺序执行自检。**前 3 项是防幻觉关键项，必须实际执行工具调用验证，不能仅目测。**

### 7.1 来源真实性抽查（最关键）

防止 AI 为了格式好看而编造行号 / 文件路径。

1. 从 `business-flows.md` 和 `domain-model.md` 随机抽取 **5 条 `来源: xxx.java:45` 形式的引用**
2. 对每条引用：
   - 用 `Glob` 或 `Read` 确认**文件存在**
   - 用 `Read` 读取**行号附近的代码**（±5 行），确认与说明匹配
3. 如发现 ≥ 1 条引用失实 → 将该引用改为 `待补充（需人工确认）`，并**重新抽查 5 条**，直到全部通过

### 7.2 实体字段真实性抽查

1. 随机抽取 `domain-model.md` 中 **3 个实体的字段清单**
2. 对每个实体用 `Read` 打开源文件，对比字段名、类型、注解
3. 发现虚构字段 → 删除；字段缺失 → 补齐

### 7.3 结构完整性

- [ ] `docs/project-overview/` 下 7 个文件都已生成（README / domain-model / business-flows / architecture / dependencies / deployment / development）
- [ ] `README.md` 头部已写入 `<!-- DOC_META: last_commit=..., generated=... -->` 锚点（非 git 仓库填 `none`）
- [ ] `README.md` 的目录列表链接到其他 6 个章节文件，链接可点击（相对路径正确）

### 7.4 内容质量

- [ ] 所有章节都有实质内容或明确标注「待补充（需人工确认）」，没有空壳占位符
- [ ] 所有 Mermaid 图表语法正确（参与者 / 状态 / 关系名称无错字）
- [ ] 没有出现 `example-output.md` 中的虚构值（如 `Spring Boot 2.7.5`、`ORD{yyyyMMddHHmmss}{随机4位}`、"连续登录失败 5 次锁定"等）被当作当前项目事实写入
- [ ] 核心实体数量 ≤ 15，主要流程数量 ≤ 8；超出部分已移入表格罗列

### 7.5 格式细节

- [ ] 专业术语使用一致（同一概念不用多种译法）
- [ ] 中英文混排时英文词前后有空格

---

## 分析技巧

### 代码推断技巧

信息不完整时，从代码推断但标注 `[推断]`：
- **项目用途**: 从 Controller 端点名称推断
- **业务规则**: 从 Service 层验证逻辑推断
- **数据关系**: 从 ORM 注解或 SQL 查询推断
- **集成服务**: 从配置文件 key 名称推断

### 使用工具高效分析

以下是**分析操作**，在所在平台用对应工具完成：

1. **语义级探索**（Claude Code: `Agent` + `subagent_type=Explore`）
   适合开放式问题，例如"Where are the main entity classes defined?" / "How is authentication implemented?"
   注：Claude Code 没有独立的 `SemanticSearch` 工具，语义搜索由 Explore 子 agent 组合 Grep/Glob/Read 完成。

2. **按内容正则搜索**（`Grep`）：如 `@Entity`、`@RestController`、`@Transactional`

3. **按文件名模式查找**（`Glob`）：如 `**/*Controller.java`、`**/entity/*.java`

### 处理大型项目

**规模分档**（按非依赖源文件数，即 Step 0.5 中 `git ls-files | grep -Ev '...' | wc -l` 的结果）：

| 规模 | 策略 |
|------|------|
| < 100 文件 | 常规流程，Step 1-6 顺序执行 |
| 100-500 文件 | 采样分析 + 严格执行核心筛选（Step 2.3 / 3.2 的上限） |
| 500-2000 文件 | 并行派发子 agent 分模块分析，每模块 3-5 个代表文件 |
| > 2000 文件 | 必须并行 + 分批产出中间摘要（见下"context 管理"） |

**并行派发子 agent**（Claude Code 用 `Agent`，其他平台用等价 dispatch；无此能力则顺序 + 见下"无并行时的 context 管理"）：

```
子任务 1: 分析用户模块（entity/User*, service/User*, controller/User*）
子任务 2: 分析订单模块（entity/Order*, service/Order*, controller/Order*）
子任务 3: 分析支付模块（entity/Payment*, service/Payment*, client/*Pay*）
```

每个子任务输出结构化结果（领域模型片段 + 业务流程片段），主 agent 汇总去重。

#### 无并行能力时的 context 管理

平台无 subagent / dispatch 能力时，顺序执行但必须压缩中间产出，避免 context 溢出：

1. **分批读取**：每批 ≤ 20 个文件，读完立即提炼结构化摘要（实体名 + 字段清单 + 方法签名），**不保留原始源码**
2. **按模块写入**：每分析完一个模块立即写入对应的 `docs/project-overview/*.md` 片段，然后清除该模块的源码 context
3. **利用 Grep 而非 Read**：优先用 Grep 统计匹配数量和位置，只在需要详细内容时才用 Read
4. **必要时分多次调用**：如果单次会话 context 不够，提示用户"已完成 [模块 A, B]，请在新会话中继续其他模块"

Monorepo 处理策略见 [references/language-hints.md](references/language-hints.md) 的 "Monorepo / 多模块项目" 小节。

---

## 最佳实践

1. **保持客观**: 基于代码事实，避免主观评价
2. **使用图表**: 复杂关系用 Mermaid 展示
3. **提供上下文**: 不仅说"是什么"，还要说"为什么"（如果代码注释或 commit 里有）
4. **标注来源**: 重要信息标注来源文件
5. **宁缺毋滥**: 找不到来源就写「待补充」，不要用示例值填充
