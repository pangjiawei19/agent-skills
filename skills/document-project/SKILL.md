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
- `language-hints.md`：Step 1 识别项目类型后加载对应语言的小节，Step 1.5（领域识别）、Step 2 / 3 / 5 复用；Step 4.5（系统架构图）加载"架构组件识别"小节
- `output-templates.md`：Step 1-5 各自产出前加载对应小节；Step 6 组装时加载 Step 6 骨架（含 DOMAIN_MAP 格式、项目层 + 领域层模板、milestones.md 模板）
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

## 全局原则：数据来源

**适用于所有 Step。先读后写，宁缺毋滥。**

1. **只写从代码、配置、构建文件、README、CI 配置中可直接读出或合理推断的内容。**
2. **找不到来源 → 写 `待补充`**，不要凭经验或示例脑补。
3. **模板中的具体值（如 `Java 11+`、`./gradlew build`）仅为格式示例，不是默认值**——必须替换为从当前项目读取到的实际值。
4. **重要断言标注来源**：如 `Java 17 (来源: pom.xml <java.version>)`。

**统一的"待补充"格式**（显式可见，便于人工找到并补上）：

```markdown
> ⚠️ 待补充（需人工确认）：<此处提示期望内容或推不出的原因>
```

---

## 输出路径规范（固定）

本 skill 生成**两层文档结构**：

- **项目层** `docs/project-overview/`：非业务的项目级内容（架构、依赖、部署、开发约定）
- **领域层** `docs/domains/<domain>/`：所有业务内容——实体、流程、API 接口，一域一目录

```
docs/
├── project-overview/
│   ├── README.md              # DOC_META + DOMAIN_MAP + 项目背景 + 技术栈 + 核心功能 + 域索引
│   ├── architecture.md        # 架构模式、系统架构图、目录结构、领域划分表、ER 主图
│   ├── milestones.md          # 里程碑（历史 + 未来）
│   ├── dependencies.md        # 外部依赖
│   ├── deployment.md          # 部署说明
│   └── development.md         # 开发指南
└── domains/
    ├── README.md              # 领域清单
    └── <domain>/
        ├── README.md          # 领域概览 + 对外接口（REST / 事件）
        ├── domain-model.md    # 本域所有实体
        └── flows.md           # 本域所有流程
        # 小域可退化为单 README.md（阈值见 Step 6）
        # API ≥ 20 时可拆出 api.md（可选）
```

**为什么这样设计**：业务内容全部聚合到 `domains/`，每个域自包含。跨域关系**通过链接**而不是"抽共性到全局层"表达——代价是几个链接跳转，收益是心智模型简单、增量更新无歧义、每次业务改动只影响一个 `domains/<x>/`。

### 三条必守的归属规则

防止同一事实在多个域重复描述导致 drift，Step 2/3 必须按下面规则执行。

**规则 1：实体归属唯一一个域（Owning Domain）**

每个实体归属**且仅归属**一个域，其他域只能**引用**、不能重复定义。

- **归属判定**：实体定义文件路径命中哪个域的 `paths` → 归那个域
- **跨域引用写法**：被其他域用到时，只写字段名 + 引用链接。示例：Order 实体的 `userId` 字段描述写 `引用 [User](../user/domain-model.md#user)`，不复述 User 的字段

**规则 2：跨域流程归属唯一一个域**

| 流程类型 | 归属域 | 判定依据 |
|---------|-------|---------|
| 同步调用链（A → B） | **发起方 A**（入口 Controller 所在域） | 业务语义从发起方起点 |
| 事件驱动（B 发事件，A 消费并处理） | **消费方 A** | 业务动作发生在 consumer |
| 纯编排（Saga / 工作流引擎） | **编排所在域**（通常有单独的 workflow/saga 域） | 编排代码的归属域 |

- **跨域序列图约定**：其他域参与者标注为 `ServiceName<br/>[<domain> 域]`，关键步骤文字加链接到被调用域的文档
- **反向索引表**：当本域的某个 Service 被其他域的流程调用，在本域 `flows.md` 末尾加"被跨域流程调用"表格（只列接口 + 调用方域 + 跨域流程链接，不复述流程内容）

**规则 3：API 清单默认放在 domain README.md**

`domains/<x>/README.md` 的"对外接口"节罗列本域所有 REST 端点、事件发布、事件订阅。单域 API **≥ 20 个**时才拆出独立 `api.md`。

### 其他约定

- **DOC_META 和 DOMAIN_MAP 锚点**都写在 `project-overview/README.md` 头部（格式见 `references/output-templates.md`）
- **单领域项目**（Step 1.5 识别结果只有 1 个域）退化为无 `domains/` 的平铺结构：`project-overview/` 下新增 `domain-model.md` 和 `flows.md` 装业务内容；DOMAIN_MAP 仍写入（单条目）为未来演化留接口

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

### 0.4 提取上次生成的 commit 锚点 + DOMAIN_MAP

读取 `docs/project-overview/README.md` 头部的两个机器可读锚点：

```markdown
<!-- DOC_META: last_commit=abc123def456, generated=2026-04-13 -->

<!-- DOMAIN_MAP
order:
  paths:
    - src/main/java/com/xxx/order/**
  entities: [Order, OrderItem]
shared:
  entities: [User, Product]
-->
```

- `last_commit` 固定 **12 位**短 hash（非 git 仓库填 `none`）
- `DOMAIN_MAP` 是 YAML 格式，定义**代码路径 → 业务域**的映射（增量更新的 SoT）

处理分支：

- **DOC_META 找到 + DOMAIN_MAP 找到** → 进入 0.5 按域分桶
- **DOC_META 找到但 DOMAIN_MAP 缺失**（文档是旧版或被手动删） → 提示用户"DOMAIN_MAP 缺失，无法精确定位变更到域；建议全量重生成以重建映射"
- **DOC_META 未找到** → 提示用户"未找到版本锚点，建议全量重生成"；若用户坚持增量，尝试用 `git log -1 --format='%h' --abbrev=12 -- docs/project-overview/README.md` 推断基准 commit；该命令也返回空则**强制走全量**并告知用户

### 0.5 判断变更规模 + 按域分桶

**第 1 步：结构性变更检查**（短路逻辑，命中即提示用户"检测到结构性变更，建议全量重生成"）：
- 构建文件变动（`pom.xml` / `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml`）
- 顶层目录新增或删除（如新增 `apps/`、`services/`）
- 主类 / 入口文件变动
- 数据库迁移文件新增
- **DOMAIN_MAP 需要扩展**（第 3 步的 `unknown` 桶非空时）

**第 2 步：变更文件占比**：

```bash
CHANGED=$(git diff <last_commit> HEAD --name-only | wc -l)
TOTAL=$(git ls-files | grep -Ev '(^|/)(node_modules|vendor|dist|build|target|\.lock|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|go\.sum)' | wc -l)
git diff <last_commit> HEAD --stat
```

| 占比（CHANGED / TOTAL） | 模式 |
|------------------------|------|
| `< 10%` | **增量更新** |
| `10%-30%` | **增量更新**（受影响域可能较多，逐个重扫） |
| `> 30%` | 提示用户"变更规模较大，建议全量重生成" |

**第 3 步：按 DOMAIN_MAP 分桶**（增量更新的核心）：

对 `git diff <last_commit> HEAD --name-only` 的每个文件路径，按 DOMAIN_MAP 分类到以下桶：

| 桶 | 匹配规则 | 影响的文档 |
|----|---------|----------|
| `bucket[<domain>]` | 路径命中某 domain 的 `paths` glob | `domains/<domain>/` 下的文件 |
| `bucket[structural]` | 构建文件、CI、Dockerfile、Makefile、配置根目录 | `project-overview/{architecture,dependencies,deployment}.md` |
| `bucket[meta]` | README、CONTRIBUTING、lint、commitlint | `project-overview/{README,development}.md` |
| `bucket[unknown]` | 都不命中 | **需要用户介入**：停下来问"这些文件应该归哪个域？要新增领域还是扩展现有 paths？" |

⚠️ `bucket[unknown]` 非空时**硬停**等用户答复，不要默默跳过——忽略会导致文档盲区越来越大。

**跨域影响**：改某个域的代码可能引起其他域的反向索引表需要更新（如新增了一个会被其他域调用的 Service）。这在 Step 3.2 归属判定时顺带处理，不单独建桶。

### 执行模式导航

- **增量更新**：按 Step 0.5 分桶结果对各桶执行对应 Step；完成后更新 `project-overview/README.md` 头部 DOC_META 锚点（DOMAIN_MAP 通常不变，用户新增域时同步更新）。
- **全量生成**：依次执行 Step 1 → 1.5（硬停等确认） → 2 → 3 → 4 → 5 → 6 → 7，每步完成后更新 Task 状态。

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

### 1.4 项目背景 + 技术栈分类 + 里程碑数据采集

本子步骤采集"非业务的项目级信息"，与域无关，不依赖 Step 1.5 DOMAIN_MAP。

#### 1.4.1 项目背景提取

从以下来源推断，写入 `project-overview/README.md`：

| 要素 | 数据源（按优先级） | 推不出时 |
|------|------------------|---------|
| 业务背景 | `README.md` 的引言/Overview/About 节、`package.json` description | `> ⚠️ 待补充（需人工确认）：项目的业务背景、要解决的问题` |
| 目标用户 / 使用场景 | `README.md` 的"Who is this for" / "Use cases" / 权限配置里的角色 | 同上格式，注明"目标用户" |
| 核心价值 | `README.md` 的 Features / Why / Highlights 节 | 同上格式 |

**重要**：项目背景属于 AI 最容易幻觉的部分（没有强约束的文字）。遵守上方全局原则——读不到就写"待补充"，不要从项目名脑补。

#### 1.4.2 技术栈分类

从 1.2 已提取的依赖清单 + 配置文件分类：

| 类别 | 典型依赖信号 |
|------|-------------|
| 后端框架 | Spring Boot / NestJS / FastAPI / Gin / Actix |
| 前端框架 | React / Vue / Next.js / Nuxt（从 `package.json` 或子模块推断） |
| 数据存储 | MySQL / PostgreSQL / MongoDB / Redis / Elasticsearch（从驱动依赖 + 配置 URL） |
| 消息队列 | Kafka / RabbitMQ / RocketMQ / Pulsar |
| DevOps | Docker / GitHub Actions / GitLab CI（从 Dockerfile + `.github/workflows/*`） |
| 监控 | Prometheus / Grafana / Sentry / DataDog SDK |
| 鉴权（可选） | Spring Security / Keycloak / Auth0 / Passport |
| 第三方集成（可选） | 支付 SDK / OSS SDK / 短信 / 邮件服务 |

输出精简版（每类一行），详细版本留给 `dependencies.md`。找不到的类别**省略**，不要写"无"。

详细的依赖命名信号按语言见 [references/language-hints.md](references/language-hints.md) 的"架构组件识别"小节。

#### 1.4.3 里程碑数据采集

采集命令：

```bash
# 历史 tag 及对应 commit 信息
git tag --sort=-creatordate | head -20
git log --tags --simplify-by-decoration --pretty='format:%h %D %ad %s' --date=short | head -30

# CHANGELOG（如果有）
# 读取 CHANGELOG.md 全文
```

数据源策略：
- **有 git tag**：按 tag + 日期 + tag message 生成历史里程碑，每个 tag 对应一行
- **无 tag 但有 CHANGELOG.md**：按 CHANGELOG 版本节生成
- **两者都没有**：里程碑文件**仍生成**，但"历史里程碑"整块写 `> ⚠️ 待补充（需人工确认）：未发现 git tag 或 CHANGELOG`
- **未来规划**：无论历史如何，都写 `> ⚠️ 待补充（需人工确认）：未来里程碑需人工规划填写`

输出格式见 [references/output-templates.md](references/output-templates.md) 的 Step 1 和 Step 6 小节。

---

## Step 1.5: 领域识别（⚠️ 硬停等用户确认）

本步只在**全量生成**时执行；增量更新直接使用 DOMAIN_MAP。

### 1.5.1 推断领域划分

按项目类型选择启发式（详见 [references/language-hints.md](references/language-hints.md) 的"领域识别"小节）。核心思路：

- **Java / 按 package**：`com.xxx.<domain>.*` 中的 `<domain>` 段通常就是业务域
- **Node.js / Python / Go**：`modules/<domain>/` 或 `<domain>/{controller,service}` 结构
- **Monorepo**：每个 `apps/<name>` 或 `services/<name>` 是一个域
- **扁平结构**：按 `*Controller` / `*Service` 命名前缀聚类（`OrderController` + `OrderService` → `order` 域）

### 1.5.2 输出推断结果 + 硬停等用户确认

**全量生成中此步骤必须硬停等用户确认**。不要擅自跳过或自行写入 DOMAIN_MAP——领域划分是后续所有增量更新的稳定基础，划错一次会长期污染文档。

以下面的格式输出推断结果给用户：

```markdown
## 推断的领域划分

| 领域 | 推断依据 | 覆盖 paths | 归属本域的核心实体 |
|------|---------|-----------|-------------------|
| order | `com.xxx.order` package 下有 12 个类，含 OrderController/OrderService | `src/main/java/com/xxx/order/**` | Order, OrderItem |
| payment | `com.xxx.payment` package 下有 5 个类 | `src/main/java/com/xxx/payment/**` | Payment, Refund |
| user | `com.xxx.user` 下有 UserController/UserService（被 order、payment 引用） | `src/main/java/com/xxx/user/**` | User, UserProfile |

## 跨域引用预览（供参考，不改变归属）
- `User`（归 user 域）被 order、payment 引用 → order、payment 的文档通过链接引用
- `Product`（归 catalog 域）被 order、inventory 引用

**请确认或修改上述划分后回复我**，例如：
- "确认"
- "把 trade 目录也划到 order 域"
- "UserProfile 应该归 account 域而不是 user"
- "inventory 应该单独成域，paths 是 xxx"

确认后我会写入 DOMAIN_MAP 并继续生成文档。
```

然后**停止后续 Step**，等待用户回复。不要说"我先继续 Step 2，后面再调整"——后续步骤依赖 DOMAIN_MAP。

### 1.5.3 单领域项目

如果推断只有 1 个业务域（常见于小型 CLI 工具、单用途微服务），告知用户"本项目识别为单领域，将生成平铺结构（无 `domains/` 子目录）"，让用户确认即可。DOMAIN_MAP 仍写入（单条目），为未来演化留接口。

### 1.5.4 用户回复后写入 DOMAIN_MAP

用户确认/修改后，按最终版 DOMAIN_MAP 继续执行 Step 2。DOMAIN_MAP 将在 Step 6 写入 `project-overview/README.md` 头部。

---

## Step 2: 领域模型提取

### 2.1 定位实体类

按项目类型选择查找策略，详见 [references/language-hints.md](references/language-hints.md) 的"实体定位"小节。

### 2.2 分析实体关系

识别主键/外键、一对多/多对多、继承、组合关系。优先使用框架注解（`@OneToMany`、`gorm` 标签、Prisma schema 等）作为事实来源。

### 2.3 筛选核心实体 + 按域归属

**先筛选核心实体**（大项目可能有 100+ 实体，全量详述会压垮 context）：

**纳入核心实体的条件（满足任一）**：
- 被 ≥ 2 个 Service / Controller 直接操作（用 Grep 统计引用次数）
- 在代码中作为 `@OneToMany` / `@ManyToOne` / `@ManyToMany` 等关系的**主表或从表出现 ≥ 2 次**
- 是聚合根（DDD 项目）或 `@Entity` 标注为主表
- 字段数 ≥ 5（小的 join 表、枚举表一般不是核心）

**数量上限**：每个域核心实体 **≤ 10 个**。超出时用末尾表格罗列。

**按域归属**（归属判定规则见上方归属规则 1）：

- 符合规则的实体写入 `docs/domains/<domain>/domain-model.md`
- **跨域引用检测**：对每个实体用 Grep 统计被引用位置，按引用方文件路径反查 DOMAIN_MAP 得到引用域列表。结果用于两件事：
  1. **归属域的文档中**标注"被 [domain-a, domain-b] 引用"（让读者知道改动影响面）
  2. **引用方的文档中**把该实体作为字段类型时，写链接指向归属域，不复述字段
- **路径未命中任何域的实体**（少见，如 shared lib 下的通用模型）：Step 1.5 硬停时用户已确认归属，按确认结果走；或新增一个 `shared-lib` 域装这类代码

**筛选不到实体时**（如无 ORM 的 CLI 项目）：转而分析主要数据结构（DTO、Value Object、Response 类型），标题改为"核心数据结构"。

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

### 3.2 筛选主要业务流程 + 按域归属

**先筛选主要流程**（大项目可能有 50+ Controller 方法，全部画序列图不现实）：

**纳入主要流程的条件（满足任一）**：
- 围绕核心实体的**创建 / 状态变更**（如"创建订单"、"支付"、"审核通过"）
- 跨 ≥ 3 层调用（Controller → Service → Repository/External）
- 涉及**外部服务调用**（支付网关、MQ、邮件、第三方 API）
- 涉及**状态机**（订单状态、审批流等）
- 涉及**分布式锁 / 事务边界**

**数量上限**：每个域主要流程 **≤ 5 个**。超出时其余端点用表格罗列：`| 端点 | 方法 | 入口 Controller | 简述 |`。

**按域归属**（归属类型见上方归属规则 2）：

**追踪与归属的执行方式**：
1. 从入口点开始（Controller / Handler / 事件监听器）
2. 按入口文件路径 + DOMAIN_MAP 判定归属域
3. 追踪 Service 调用链（Grep 每层调用目标），记录涉及的**其他域**
4. 识别数据访问、外部调用、事务边界和异常处理
5. **仅写入归属域的 `flows.md`**，画完整序列图

**跨域序列图约定**（原则见上方归属规则 2；参与者示例：`PaymentService<br/>[payment 域]`；链接示例：`调用 [PaymentService.charge](../payment/README.md#charge)`）。

**反向索引表**（本域的 Service 被其他域流程调用时）：

在被调用域的 `flows.md` 末尾追加一节：

```markdown
## 被跨域流程调用

| 本域接口 | 调用方域 | 跨域流程 |
|---------|---------|---------|
| `PaymentService.charge` | order | [下单支付](../order/flows.md#下单支付) |
```

这样被调用域读者能知道"我的代码被哪些跨域流程依赖"，改 API 前会去看影响面。**不要在被调用域重复画这个跨域流程的序列图**——权威只在归属域一份。

### 3.3 识别状态机

对核心实体（尤其是 `Order`、`Task`、`Workflow` 等）检查是否存在状态字段 + 状态转换逻辑：
- 枚举类（`OrderStatus.java`、`*State.java`）
- 状态机库（Spring Statemachine、`squirrel-foundation`、XState、自实现的 `switch-case`）
- 状态变更方法（`markAs*`、`transitionTo*`）

找到则画 `stateDiagram-v2`，标注来源文件。

### 3.4 绘制流程图

使用 Mermaid `sequenceDiagram` 或 `stateDiagram-v2`。

输出格式见 [references/output-templates.md](references/output-templates.md) 的 Step 3 小节。

### 3.5 核心功能数据采集（供 Step 6 组装使用）

在完成各域的 Controller/Service 梳理后，聚合成**用户视角**的核心功能清单，**记录备 Step 6 写入 `project-overview/README.md`**。

**数据源**（按优先级）：
1. 各域 Controller 的 REST 端点（如 `POST /api/orders` → "下单"）
2. 事件发布（如 `OrderCreated` → "触发订单创建通知"）
3. 定时任务（如 `@Scheduled` → "每日账单结算"）

**组织方式**：按业务域分组，每组 3-5 个功能。

**写作原则**：
- **用户视角**：写"下单"、"取消订单"，不写"调用 OrderController.create"
- **从端点名称推断功能名**，命名歧义时标 `[推断]`
- 每个功能后记录对应域的文档链接：`[下单](../domains/order/README.md#下单流程)`
- **只列用户能做的动作**，内部调用、管理后台接口另列或省略

**数量控制**：全量核心功能清单 **≤ 20 个**。超出时只留高频 / 高价值的 20 个，其余以"完整端点见各域 README"收尾。

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

### 4.4 渲染领域划分表 + ER 主图

在 `architecture.md` 里新增"领域划分"小节，包含两部分：

1. **领域划分表**：将 Step 1.5 确认的 DOMAIN_MAP 渲染为表格（域名 / paths / 核心实体 / 一句话职责）
2. **跨域 ER 主图**（Mermaid `erDiagram`）：**只画涉及跨域引用的实体关系**（如 Order → User、Payment → User），域内实体细节留给各域的 `domain-model.md`

目的：让读 architecture.md 的人一眼看到目录结构、业务域划分、以及跨域实体关系这三件事。不画全量 ER（全量在各域内各自画），避免这张图随实体增加而失控。

### 4.5 系统架构图（C4 Context/Container 级别）

在 `architecture.md` 的"架构模式"节后新增"系统架构图"节，用 Mermaid `flowchart` 画部署拓扑 / 组件关系。

**画什么**（自上而下分组）：
- **外部 actor**：终端用户、管理员、外部系统（从 README 或权限配置推断；没有就画一个通用 `User`）
- **前端**：Web / 移动端 / 管理后台（从 `package.json`、README 提及、共存的子目录推断）
- **网关 / 负载均衡**：nginx / ALB / APISIX 等（从 `Dockerfile`、`docker-compose.yml`、CI 配置推断；推不出就**省略该节点**）
- **后端服务**：按 `@SpringBootApplication` / `main` 入口数量 / `docker-compose.yml services` 数量决定画几个
- **数据层**：DB / 缓存 / 搜索引擎（从驱动依赖 + 配置推断）
- **消息层**：Kafka / RabbitMQ / MQ broker（从依赖 + 配置推断）
- **第三方集成**：支付 / OSS / 短信 / 邮件（从 SDK 依赖推断）

**连线原则**（从代码能看出的）：
- 后端 → 数据层：有对应的 Repository / DAO 则画连线
- 后端 → MQ：有 Producer / Consumer 则画
- 后端 → 第三方：有对应 SDK 调用则画

**推不出的部分**处理：
- 整个节点推不出（如网关）→ **不画**该节点
- 某条连线推不出（如内部服务间 RPC 调用）→ 用虚线 + `[待补充]` 标签
- 前端具体形态（Web/App/小程序）推不出 → 画一个通用 `Frontend` 节点

**图后补充一张"组件清单"表**（列出每个节点的来源证据，便于人工 review）：

| 组件 | 实际证据 | 备注 |
|------|---------|------|
| MySQL | `spring.datasource.url` in `application.yml` + `mysql-connector-j` 依赖 | |
| Kafka | `spring-kafka` 依赖 + `spring.kafka.bootstrap-servers` 配置 | |
| Nginx | `待补充` | 未在代码库发现，通常是部署层 |

详细的组件识别规则见 [references/language-hints.md](references/language-hints.md) 的"架构组件识别"小节。

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

### 6.0 数据来源原则

见上方[全局原则：数据来源](#全局原则数据来源)。Step 6 组装时同样遵循此原则——找不到来源写「待补充」，模板值必须替换为项目实际值。

### 6.1 可自动生成的章节 vs 需人工补充的章节

| 章节 | 数据来源 | 找不到来源时 |
|------|---------|------------|
| 项目简介 - 类型/技术栈/版本 | 构建文件 | 从代码推断，标注 `[推断]` |
| 项目简介 - 业务背景/目标用户/核心价值 | `README.md` 引言、`package.json` description | **整块写"待补充"**，不要脑补 |
| 技术栈总览 | 依赖清单分类（Step 1.4.2） | 找不到的类别省略，不写"无" |
| 核心功能列表 | 各域 Controller 端点 + 事件 + 定时任务（Step 3.5） | 命名歧义标 `[推断]`；都推不出时整节写"待补充" |
| 核心领域模型 | 实体类代码 + 注解 | **字段级**：略过无法确认的字段；**实体级**：无法确认核心字段则降级到"次要实体"表格 |
| 业务流程 | Controller + Service 调用链 | 只画能追踪到的部分，标注 `[部分流程未覆盖]` |
| 项目结构 | 目录扫描 + DOMAIN_MAP | 客观陈述，无需推断 |
| **系统架构图** | Dockerfile / docker-compose / 依赖 / 配置 | 推不出的节点不画；推不出的连线用虚线 + `[待补充]` |
| **里程碑 - 历史** | `git tag` + `CHANGELOG.md` | 两者都无时整块写"待补充（未发现 git tag 或 CHANGELOG）" |
| **里程碑 - 未来** | — | 整块写"待补充（需人工规划填写）" |
| 外部依赖 | 构建文件 + 配置文件 | 无则不列 |
| 部署说明 - 环境要求 | 构建文件、`Dockerfile`、`docker-compose.yml`、CI | 未声明组件写 `待补充` |
| 部署说明 - 启动步骤 | `README`、`Makefile`、`scripts`、`CMD`、CI workflow | 找不到则写 `待补充（未在代码库中发现启动脚本）` |
| 部署说明 - 配置说明 | `application-example.yml`、`.env.example`、配置类 | 不要编造配置项 |
| 开发指南 | `CONTRIBUTING.md`、lint 配置、git hooks、`CODEOWNERS` | 找不到则整节写 `待补充（建议人工编写）` |

### 6.2 判断每个域是单文件还是拆分模式

**单文件模式**（默认）：`domains/<x>/README.md` 一个文件装全部内容。

**拆分模式**触发阈值（任一命中则拆为 `README.md + domain-model.md + flows.md`）：
- 本域核心实体 ≥ 4 个需要详述
- 本域主要流程 ≥ 3 个需要序列图
- 预估单文件会超过 400 行

**为什么设阈值**：小域拆成 3 个空文件比一个简洁的 README 更难读；大域塞进一个文件又会让人滚屏找不到。阈值让文档密度自适应。

### 6.3 组装并写入

按 [references/output-templates.md](references/output-templates.md) 的 Step 6 骨架，把 Step 1-5 产出按下表分发：

**项目层**（`docs/project-overview/`，6 个文件）：

| 文件 | 内容 | 来源 |
|------|------|------|
| `README.md` | DOC_META + DOMAIN_MAP + 项目简介（含背景/技术栈/目标用户）+ 核心功能 + 域索引 | Step 1 + 3.5（3.5 采集数据，此处写入文件） |
| `architecture.md` | 架构模式 + **系统架构图** + 目录结构 + 领域划分表 + 跨域 ER 主图 | Step 4 |
| `milestones.md` | 历史里程碑（git tag / CHANGELOG 提取）+ 未来规划（待补充） | Step 1.4.3 |
| `dependencies.md` | 依赖表格、第三方服务 | Step 5 |
| `deployment.md` | 环境要求、配置说明、启动步骤 | Step 6 |
| `development.md` | 本地开发、代码规范、提交规范、FAQ | Step 6 |

**领域层**（`docs/domains/`）：

| 文件 | 内容 |
|------|------|
| `domains/README.md` | 领域清单（表格：域名 / 职责 / 核心实体 / 文档链接） |
| `domains/<X>/README.md`（单文件模式） | 领域概览 + 对外接口 + 本域实体 + 本域流程 |
| `domains/<X>/README.md`（拆分模式） | 领域概览 + 对外接口 + 实现位置 + 章节链接 |
| `domains/<X>/domain-model.md`（拆分模式） | 本域所有实体详情 |
| `domains/<X>/flows.md`（拆分模式） | 本域所有流程 + 状态机 + 反向索引表 |
| `domains/<X>/api.md`（可选，API ≥ 20 时） | 完整 API 清单 |

**`project-overview/README.md` 头部必须同时写入两个锚点**：

```markdown
<!-- DOC_META: last_commit=abc123def456, generated=2026-04-21 -->

<!-- DOMAIN_MAP
<Step 1.5 确认的映射，YAML 格式>
-->
```

**章节间互链规则**：
- `project-overview/README.md` 目录项链接到本层其他文件 + `../domains/README.md`
- 每个 `domains/<x>/` 下文件头部加"回到：[领域清单](../README.md) · [项目总览](../../project-overview/README.md)"
- **跨域实体引用**：`../<other-domain>/domain-model.md#entity-name`（单文件模式下锚点在 `README.md`）
- **跨域流程引用**：`../<other-domain>/flows.md#flow-name`（单文件模式下锚点在 `README.md`）

### 6.4 先建目录再写入

```bash
mkdir -p docs/project-overview
mkdir -p docs/domains
# 对每个域：
mkdir -p docs/domains/<domain>
```

**单领域项目特例**：见上方路径规范的单领域退化规则（`project-overview/` 下新增 `domain-model.md` 和 `flows.md`，不创建 `docs/domains/`）。

### 6.5 生成摘要

给用户一段简短摘要：核心功能、主要技术栈、识别出的业务域数量及名称、每域实体/流程数量、文档保存位置。

---

## Step 7: 输出质量自检（必做）

生成后按以下顺序执行自检。**前 3 项是防幻觉关键项，必须实际执行工具调用验证，不能仅目测。**

### 7.1 来源真实性抽查（最关键）

防止 AI 为了格式好看而编造行号 / 文件路径。

1. 从各 `domains/<x>/` 下的流程与实体文档中随机抽取 **5 条 `来源: xxx.java:45` 形式的引用**
2. 对每条引用：
   - 用 `Glob` 或 `Read` 确认**文件存在**
   - 用 `Read` 读取**行号附近的代码**（±5 行），确认与说明匹配
3. 如发现 ≥ 1 条引用失实 → 将该引用改为 `待补充（需人工确认）`，并**重新抽查 5 条**，直到全部通过

### 7.2 实体字段真实性抽查

1. 随机抽取 `domain-model.md` 中 **3 个实体的字段清单**
2. 对每个实体用 `Read` 打开源文件，对比字段名、类型、注解
3. 发现虚构字段 → 删除；字段缺失 → 补齐

### 7.3 结构完整性

- [ ] `docs/project-overview/` 下 6 个文件都已生成（README / architecture / milestones / dependencies / deployment / development）
- [ ] `project-overview/README.md` 头部同时写入 `<!-- DOC_META: ... -->` 和 `<!-- DOMAIN_MAP ... -->` 锚点
- [ ] `README.md` 有"项目背景 / 技术栈总览 / 核心功能"三个新节（推不出的部分用统一"待补充"格式）
- [ ] `architecture.md` 含"系统架构图"节（Mermaid flowchart）+ 组件清单表
- [ ] `milestones.md` 已生成（即使无 tag/CHANGELOG 也要生成空壳 + 待补充）
- [ ] 多领域项目：`docs/domains/README.md` + 每个 `domains/<X>/README.md` 都已生成
- [ ] 单领域项目：退化结构正确（无 `docs/domains/`，`project-overview/` 下含 `domain-model.md` 和 `flows.md`）

### 7.4 链接完整性（防幻觉关键项，必须实际工具验证）

- [ ] DOMAIN_MAP 中所有 `paths` glob 都能 Glob 到至少 1 个实际文件（paths 失效会让增量更新错乱）
- [ ] `project-overview/README.md` 的目录链接到的文件**都存在**
- [ ] 每个 `domains/<X>/` 下文件头部的"回到"链接正确（两条：领域清单、项目总览）
- [ ] 跨域引用链接（`../<other-domain>/domain-model.md#xxx` 或 `../<other-domain>/flows.md#xxx`）随机抽查 3 条：目标文件存在且锚点存在
- [ ] 若存在跨域调用，**反向索引表**已生成在被调用域的 `flows.md` 末尾

### 7.5 内容质量

- [ ] 所有章节有实质内容或明确标注「待补充（需人工确认）」，没有空壳占位符
- [ ] 所有 Mermaid 图表语法正确（参与者 / 状态 / 关系名称无错字）
- [ ] 没有出现 `example-output.md` 中的虚构值被当作当前项目事实写入
- [ ] 单域核心实体 ≤ 10、主要流程 ≤ 5；超出部分已移入表格罗列
- [ ] 跨域 ER 主图只画涉及跨域引用的实体关系，不含域内细节

### 7.6 格式细节

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
