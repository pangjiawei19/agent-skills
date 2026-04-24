---
name: document-project
description: Analyze existing codebase and generate comprehensive project documentation including overview, domain models, business flows, architecture, and dependencies. Use when the user asks to document a project, create project documentation, analyze codebase structure, or mentions terms like "项目文档", "整理文档", "项目说明", "代码分析", "架构梳理", "onboarding 文档".
---

# Project Documentation Generator

从现有代码库生成两层项目文档：**项目层**（非业务的项目级内容）+ **领域层**（业务内容按域拆分）。

**配套使用**：`bgp-document-iteration` skill 用于记录每次 feature 分支的迭代改动,与本 skill 形成套件——本 skill 维护**项目现状**(随代码演进),`bgp-document-iteration` 记录**变更历史**(不可变时间线)。

## 工具兼容性

本 skill 使用 **Claude Code** 工具名（`Glob`、`Grep`、`Read`、`Bash`、`Agent`）。跨平台映射见 [references/tool-mapping.md](references/tool-mapping.md)。

## 配套文件

- [references/output-templates.md](references/output-templates.md) — 两层文档骨架模板（Step 7 组装时加载）
- [references/language-hints.md](references/language-hints.md) — 按语言/框架的定位提示（Step 1 识别项目类型后加载对应语言小节；Step 2/3/5 复用）
- [references/tool-mapping.md](references/tool-mapping.md) — 跨 Agent 平台工具映射（仅非 Claude Code 平台需要）

## 不适用场景（先判断）

如果目标仓库属于以下情况之一，本 skill **不适用**——应直接告知用户，不要硬生成空洞文档：

- **纯文档仓库**（博客、知识库，源代码 < 20 个非配置文件）
- **教学示例仓库**（README 明确标明 tutorial / example / demo / starter / template / boilerplate）
- **配置仓库**（仅含 YAML / JSON / Terraform / k8s manifests，无业务代码）
- **玩具项目**（单 main 文件 + < 5 个源文件 — 直接写 README 更合适）
- **空仓库或仅有构建骨架**（无业务代码）
- **单领域项目**（扫描后只能识别出 1 个业务域，两层结构过重）

**判断方式**：Glob 统计非依赖源文件数量 → 读 README 前 50 行判断性质 → 命中任一条件则输出：

> 当前仓库看起来是 [类型]，不适合生成两层项目文档。建议改为：[根据类型给建议]。如仍需生成，请告知。

等用户确认后再继续；否则跳过本 skill。

---

## 全局原则

### 1. 数据来源（适用于所有 Step）

**先读后写，宁缺毋滥。**

- 只写从代码、配置、构建文件、README、CI 配置中**可直接读出或合理推断**的内容
- 找不到来源 → 写 `待补充`，**不要凭经验或示例脑补**
- 模板中的具体值（如 `Java 11+`、`./gradlew build`）仅为格式示例，**不是默认值**——必须替换为实际值
- 重要断言标注来源：`Java 17 (来源: pom.xml <java.version>)`

**统一的"待补充"格式**（显式可见，便于人工找到并补上）：

```markdown
> ⚠️ 待补充（需人工确认）：<此处提示期望内容或推不出的原因>
```

### 2. 归属规则（Step 3 / 4 复用）

每条业务事实**只在一个地方**有权威描述，其他地方通过链接引用，防止 drift。

**实体归属**：每个实体归属**且仅归属**一个域。
- 归属判定：实体定义文件路径命中哪个域的 `paths` → 归那个域
- 跨域引用写法：只写字段名 + 链接，不复述字段。例：Order 的 `userId` 字段描述写 `引用 [User](../user/README.md#user)`

**流程归属**：

| 流程类型 | 归属域 |
|---------|-------|
| 同步调用链（A → B） | **发起方 A**（入口 Controller 所在域） |
| 事件驱动（B 发事件，A 消费） | **消费方 A**（业务动作发生处） |
| 纯编排（Saga / 工作流） | **编排所在域** |

**共享基础设施**（shared-lib、util、通用 types 等）：**不作为业务域**，不进 `domains/`；在 `architecture.md` 的"目录结构"节一句话说明即可。

### 3. 跨域链接写法（统一）

所有跨域链接**统一指向 `../<other-domain>/README.md#<anchor>`**，不写 `domain-model.md` 或 `flows.md`——这样该域从单文件切到拆分模式时，引用方文档不用改。

- 实体引用：`[User](../user/README.md#user)`
- 流程引用：`[PaymentService.charge](../payment/README.md#charge)`

**拆分模式下**：`<domain>/README.md` 的"核心实体"和"主要流程"节保留跳转段（标题锚点 + 一句话 + 指向 `domain-model.md` / `flows.md` 的链接），让跨域链接始终有效。

---

## 输出路径规范

```
docs/wiki/
├── README.md                   # 项目层入口：项目背景 + 技术栈 + 核心功能 + 域索引
├── architecture.md             # 架构模式 + 系统架构图 + 目录结构 + 领域划分 + 跨域 ER
├── milestones.md               # 里程碑（历史 + 未来）
├── dependencies.md             # 外部依赖
├── deployment.md               # 部署说明
├── development.md              # 开发指南
└── domains/                    # 领域层（业务内容）
    ├── README.md               # 领域清单
    └── <domain>/
        ├── README.md           # 领域概览 + 对外接口 + （单文件模式下含实体、流程）
        ├── domain-model.md     # 本域所有实体（拆分模式）
        └── flows.md            # 本域所有流程（拆分模式）
        # API ≥ 20 时可拆出 api.md（可选）
```

**拆分触发条件**（任一命中，单文件 → 拆 `README + domain-model + flows`）：
- 本域核心实体 ≥ 4 个需详述
- 本域主要流程 ≥ 3 个需序列图
- 预估单文件会超过 400 行

---

## 执行模式：首次 vs 增量

每次调用 skill 前先 `Glob` 检查 `docs/wiki/README.md`：

- **未命中** → **首次模式**：走 Step 1-7 全量生成
- **命中** → **增量模式**：同样跑 Step 1-6 分析代码，但 Step 7 改走"重算 auto 区 + 保留人工内容"的合并逻辑

### 两层叠加的设计心智

文档由两层组成：

| 层 | 边界 | skill 行为 |
|---|------|-----------|
| **代码层**（auto 区） | HTML 注释 `<!-- auto:xxx -->...<!-- /auto:xxx -->` 包裹的块 | 每次跑**整块替换**为从代码重新算出的内容 |
| **人工层** | auto 标记**外**的所有内容：prose、业务背景、设计说明、例外情况、填过的"待补充"等 | 永不改写，原样透传 |

规则只有一条：**代码事实放 auto 区；为什么/例外/背景放 auto 区外的人工小节**。详细标记清单见 [references/output-templates.md](references/output-templates.md) 的 "auto 标记约定" 一节。

### 业务规则的切分（重要）

同一个"规则"在文档里要拆成两段：

- **代码可验证的规则** → `auto:entity:<Name>` 或 `auto:flow:<Name>` 内部，从校验/调度/状态机代码提取
- **为什么/例外/业务背景** → 紧跟 auto 块下方的"业务背景 / 例外情况"小节，人工写

这样下次代码加了新校验，skill 在 auto 区自动补上；人工写的"为什么 30 分钟"、"大客户特批"不会被覆盖。

### 混合区块：`auto:domains-table`（行级既有权威）

`architecture.md` 的领域划分表虽然标着 auto，但语义与普通 auto 块**不同**——它是"混合区"：

- **首次生成**：由 Step 2 推断填入
- **增量模式**：
  - 每一**既有行**（包括单元格内容、备注、人工改过的域名）视为**人工权威**，skill 永不覆写
  - 只在代码里出现了未命中任何既有 path 的新路径时，**追加**一行"待归属：<path> · 建议：<域>" 到表尾让用户决定

这条规则让"用户手动调整过的划分"和"用户加在行内的备注（如 `[人工改名：xxx → yyy]`）"都被保留，而 skill 仍能把新代码追加上来。

### 衍生 auto 块：`auto:domain-index` / `auto:domains-listing`

这两个块展示的域名 / 职责列表是 `auto:domains-table` 的**投影**。增量模式下按以下规则重算：

- 域名 / 文档链接文本：跟随 `auto:domains-table` 的既有行（含人工改过的名字）
- **不跟随**的情况：文档链接的 URL 路径（链接 `./domains/<x>/`）。用户改域名但未改目录时会造成链接和文本不一致——skill 不自动修复（物理 `mv` 风险高），由用户手动处理（见 README "域重命名指南"）

---

## Step 1: 项目概览

### 1.1 识别项目类型

检查构建文件：
- `pom.xml` / `build.gradle` → Java / Spring
- `package.json` → Node.js / 前端
- `requirements.txt` / `pyproject.toml` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust
- 顶层 `apps/` / `packages/` / `services/` / `pnpm-workspace.yaml` → Monorepo

识别后加载 [references/language-hints.md](references/language-hints.md) 对应语言小节。

### 1.2 一次读完构建文件（供 Step 1 和 Step 6 共用）

**一次读取，同时提取**：
- **项目元信息**（Step 1 使用）：名称、版本、技术栈、构建工具
- **完整依赖列表**（Step 6 使用）：所有 dependency 条目及版本

内部保存依赖列表，Step 6 直接引用。

### 1.3 扫描通用排查清单

优先读取：`README.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`Dockerfile`、`docker-compose.yml`、CI 配置（`.github/workflows/*`、`.gitlab-ci.yml`）、`Makefile`、`.env.example`、`openapi.yaml`。

### 1.4 项目背景 + 技术栈 + 里程碑数据

**项目背景**（从以下来源，推不出写"待补充"）：

| 要素 | 数据源（按优先级） |
|------|------------------|
| 业务背景 | `README.md` 引言/Overview/About 节、`package.json` description |
| 目标用户 | `README.md` 的"Who is this for" / 权限配置角色 |
| 核心价值 | `README.md` 的 Features / Why / Highlights 节 |

⚠️ 项目背景是 AI 最容易幻觉的部分——读不到就写"待补充"，不要从项目名脑补。

**技术栈分类**（从 1.2 依赖清单 + 配置文件）：

| 类别 | 典型依赖信号 |
|------|-------------|
| 后端框架 | Spring Boot / NestJS / FastAPI / Gin / Actix |
| 前端框架 | React / Vue / Next.js / Nuxt |
| 数据存储 | MySQL / PostgreSQL / MongoDB / Redis / Elasticsearch |
| 消息队列 | Kafka / RabbitMQ / RocketMQ / Pulsar |
| DevOps | Docker / GitHub Actions / GitLab CI |
| 监控 | Prometheus / Grafana / Sentry / DataDog |

输出精简版，详细版本留给 `dependencies.md`。找不到的类别**省略**，不写"无"。详细信号见 language-hints.md 的"架构组件识别"。

**里程碑数据**：

```bash
git tag --sort=-creatordate | head -20
git log --tags --simplify-by-decoration --pretty='format:%h %D %ad %s' --date=short | head -30
# CHANGELOG.md 全文（如有）
```

数据源策略：
- 有 git tag：按 tag + 日期 + message 生成
- 无 tag 但有 CHANGELOG：按 CHANGELOG 版本节生成
- 两者都没有：`milestones.md` **仍生成**，但"历史里程碑"整块写待补充
- **未来规划**：无论如何都写待补充（需人工规划）

---

## Step 2: 领域识别

分叉点：

- **增量模式**：直接 `Read docs/wiki/architecture.md` 的 `auto:domains-table` 块作为归属依据，**不执行下面的 2.1 / 2.2**。只对代码里**未命中任何既有 path** 的孤儿路径做最小推断，输出一组"待归属"行（由 Step 7.5 追加到表尾）。2.3 单领域判断也不重跑——既有表已定性
- **首次模式**：执行 2.1 → 2.2 → 2.3 推断并写表

### 2.1 推断划分（首次模式）

按项目类型选择启发式（详见 language-hints.md 的"领域识别"小节）。核心思路：

- **Java / 按 package**：`com.xxx.<domain>.*` 中的 `<domain>` 段通常是业务域
- **Node.js / Python / Go**：`modules/<domain>/` 或 `<domain>/{controller,service}` 结构
- **Monorepo**：每个 `apps/<name>` 或 `services/<name>` 是一个域
- **扁平结构**：按 `*Controller` / `*Service` 命名前缀聚类（`OrderController` + `OrderService` → `order` 域）

**过滤非业务目录**：`config` / `common` / `util` / `infrastructure` / `gateway` / `shared`——归入 shared 基础设施（不作业务域）。

### 2.2 输出到 architecture.md（首次模式）

把推断结果写入 `architecture.md` 的 `auto:domains-table` 块，表格包含：**域名 / paths / 归属本域的核心实体 / 一句话职责**。

### 2.3 判断单领域退出（首次模式）

如果推断结果**只有 1 个业务域**，提示用户：

> 本项目识别为单领域，两层结构过重。建议直接写一份单页 README，或确认后我会为你生成扁平的 `docs/wiki/` 目录（README + domain-model + flows）。继续请回复"继续"。

用户要求继续则用退化结构（`docs/wiki/` 下直接 `README.md` + `domain-model.md` + `flows.md`）；否则跳过本 skill。

---

## Step 3: 领域模型提取

### 3.1 定位实体类

按项目类型选择查找策略，详见 language-hints.md 的"实体定位"小节。

### 3.2 分析实体关系

识别主键/外键、一对多/多对多、继承、组合。优先使用框架注解（`@OneToMany`、`gorm` 标签、Prisma schema 等）作为事实来源。

### 3.3 筛选核心实体 + 按域归属

**先筛选核心实体**（大项目可能 100+ 实体，全量详述会压垮 context）。

**纳入条件（满足任一）**：
- 被 ≥ 2 个 Service / Controller 直接操作（Grep 统计引用次数）
- 作为 `@OneToMany` / `@ManyToOne` / `@ManyToMany` 等关系的主表或从表出现 ≥ 2 次
- 是聚合根（DDD 项目）或 `@Entity` 主表
- 字段数 ≥ 5（小 join 表、枚举表一般不核心）

**数量上限**：每域核心实体 **≤ 10 个**。超出时用末尾表格罗列。

**按域归属**（见全局原则-归属规则）：
- 归属域的 `domain-model.md` 写详情（或单文件模式下写 `README.md`）
- 引用方的文档中把该实体作为字段类型时，用链接指向归属域，**不复述字段**

**筛选不到实体时**（如无 ORM 的 CLI 项目）：转而分析主要数据结构（DTO、Value Object、Response 类型），章节改名为"核心数据结构"。

### 3.4 记录核心实体

对每个核心实体记录：
- **实体名称和用途**（标注来源文件）
- **关键字段及含义**（仅列出代码中实际存在的字段）
- **业务规则**（⚠️ 只列出代码中可验证的规则，不要凭经验脑补）
- **关联关系**

**降级规则**：如果核心字段都无法从代码确定，不要强行详述——降级到末尾的"次要实体表格"。

输出格式（含 Mermaid ER 图）见 output-templates.md 的领域层模板。

---

## Step 4: 业务流程梳理

### 4.1 识别业务入口

按项目类型定位，详见 language-hints.md 的"业务入口"小节。涵盖：REST API、GraphQL、消息队列消费、定时任务、事件处理、gRPC。

### 4.2 筛选主要业务流程 + 按域归属

**纳入条件（满足任一）**：
- 围绕核心实体的**创建 / 状态变更**（如"创建订单"、"支付"、"审核通过"）
- 跨 ≥ 3 层调用（Controller → Service → Repository/External）
- 涉及**外部服务调用**（支付网关、MQ、邮件、第三方 API）
- 涉及**状态机**（订单状态、审批流等）
- 涉及**分布式锁 / 事务边界**

**数量上限**：每域主要流程 **≤ 5 个**。超出时其余端点用表格罗列：`| 端点 | 方法 | 入口 Controller | 简述 |`。

**按域归属**（见全局原则-归属规则）：

1. 从入口点开始（Controller / Handler / 事件监听器）
2. 按入口文件路径判定归属域
3. 追踪 Service 调用链（Grep 每层调用目标），记录涉及的其他域
4. 识别数据访问、外部调用、事务边界和异常处理
5. **仅写入归属域的 `flows.md`**，画完整序列图

**跨域序列图约定**：其他域参与者标注为 `ServiceName<br/>[<domain> 域]`；关键步骤文字加链接到被调用域。链接统一用 `../<other-domain>/README.md#<anchor>`（见全局原则-跨域链接）。

### 4.3 识别状态机

对核心实体（`Order`、`Task`、`Workflow` 等）检查状态字段 + 状态转换逻辑：
- 枚举类（`OrderStatus.java`、`*State.java`）
- 状态机库（Spring Statemachine、`squirrel-foundation`、XState、自实现 `switch-case`）
- 状态变更方法（`markAs*`、`transitionTo*`）

找到则画 `stateDiagram-v2`，标注来源文件。

### 4.4 绘制流程图

使用 Mermaid `sequenceDiagram` 或 `stateDiagram-v2`。

### 4.5 核心功能清单（供 Step 7 写入 docs/wiki/README.md）

聚合各域流程为**用户视角**的核心功能清单：

**数据源**（按优先级）：
1. 各域 Controller 的 REST 端点（如 `POST /api/orders` → "下单"）
2. 事件发布（如 `OrderCreated` → "触发订单创建通知"）
3. 定时任务（如 `@Scheduled` → "每日账单结算"）

**写作原则**：
- **用户视角**："下单"、"取消订单"，不写"调用 OrderController.create"
- 从端点名称推断功能名；命名歧义标 `[推断]`
- 每个功能加对应域的链接：`[下单](./domains/order/README.md#下单流程)`
- **只列用户能做的动作**，内部调用、管理后台接口另列或省略

**数量控制**：全量 **≤ 20 个**。超出时留高频 / 高价值的 20 个，其余以"完整端点见各域 README"收尾。

---

## Step 5: 架构分析

### 5.1 扫描目录结构

使用 Glob 扫描，**深度按语言自适应**——目标是看到业务关键目录（`controller/`、`service/`、`entity/`、`handler/`、`router/` 等）：
- Java / Kotlin / Scala：6-8 层
- C#：5-7 层
- Python / Node.js / Go / Rust：3-5 层
- Monorepo：顶层 2 层定位子模块，再按上表扫描

如果按推荐深度看不到业务关键词（controller/service/handler/router/model/entity），加深 2 层；仍看不到则从 `src/` 或项目根整体扫。

**忽略目录**：`node_modules`、`target`、`build`、`dist`、`.git`、`vendor`、`__pycache__`、`.pytest_cache`、`.tox`、`.venv`、`*.egg-info`、`.next`、`.nuxt`、`.gradle`、`out`、`bin`、`obj`、`coverage`、`.idea`、`.vscode`。

> ⚠️ 不要把 `env/` 加入忽略列表——只忽略 `.venv/`、`.env/`（点开头）。

### 5.2 识别架构模式

从目录命名 + 包结构 + 关键注解推断：
- **分层架构**：Controller → Service → Repository
- **六边形架构**：Domain → Application → Infrastructure / Adapter
- **微服务架构**：多个独立服务
- **模块化单体**：按业务域划分模块

### 5.3 系统架构图（C4 Context/Container 级别）

在 `architecture.md` 的"架构模式"节后新增"系统架构图"节，用 Mermaid `flowchart` 画部署拓扑。

**画什么**（自上而下分组）：
- **外部 actor**：终端用户、管理员、外部系统
- **前端**：Web / 移动端 / 管理后台（从 `package.json`、README 提及、子目录推断）
- **网关 / 负载均衡**：nginx / ALB / APISIX（从 Dockerfile / docker-compose / CI 推断；推不出**省略该节点**）
- **后端服务**：按 `@SpringBootApplication` / `main` 入口数 / `docker-compose.yml services` 决定几个
- **数据层**：DB / 缓存 / 搜索引擎
- **消息层**：Kafka / RabbitMQ
- **第三方集成**：支付 / OSS / 短信 / 邮件

**连线原则**（从代码能看出的）：
- 后端 → 数据层：有对应 Repository / DAO 则画
- 后端 → MQ：有 Producer / Consumer 则画
- 后端 → 第三方：有对应 SDK 调用则画

**推不出的处理**：
- 整个节点推不出（如网关）→ **不画**
- 某条连线推不出（内部服务间 RPC）→ 虚线 + `[待补充]`
- 前端形态推不出 → 画通用 `Frontend` 节点

**图后补充"组件清单"表**，列每个节点的证据：

| 组件 | 实际证据 | 备注 |
|------|---------|------|
| MySQL | `spring.datasource.url` in `application.yml` + `mysql-connector-j` 依赖 | |
| Nginx | `待补充` | 未在代码库发现，通常是部署层 |

详细识别规则见 language-hints.md 的"架构组件识别"小节。

### 5.4 领域划分表 + 跨域 ER 主图

在 `architecture.md` 写两个 auto 块：

1. `auto:domains-table` — 领域划分表。**增量模式下此表是特殊区块**（既有行不动，只追加"待归属"行），具体规则见 Step 2 和 Step 7.5
2. `auto:er-diagram` — 跨域 ER 主图（Mermaid `erDiagram`），**只画涉及跨域引用的实体关系**。域内实体细节留给各域 `domain-model.md`

目的：让读 architecture.md 的人一眼看到目录、域、跨域实体关系三件事。不画全量 ER（全量在各域内画），避免这张图随实体增加而失控。

---

## Step 6: 依赖关系整理

### 6.1 使用 Step 1.2 已读取的依赖列表

直接使用 Step 1.2 已提取的依赖列表。monorepo 的子模块构建文件如 Step 1 未扫描，再补读。

### 6.2 分类依赖（按实际取舍）

参考类别，按项目实际取舍：
- **核心框架**（Web / RPC / ORM）
- **数据存储**（数据库、NoSQL）
- **缓存 / 消息队列**
- **工具库**
- **开发和测试**
- **项目特有类别**（如 ML 项目的"模型框架"、CLI 项目的"命令行解析"）

CLI / 纯库 / 纯前端项目的"数据存储"、"消息队列"等类别可直接省略，避免空表格。

### 6.3 识别外部服务

从配置文件和代码查找：第三方 API、云服务、支付网关、短信/邮件服务。每项标注配置 key 前缀和调用文件位置。

---

## Step 7: 生成完整文档

### 7.1 可自动生成的章节 vs 需人工补充的章节

| 章节 | 数据来源 | 找不到时 |
|------|---------|---------|
| 项目简介 - 类型/技术栈/版本 | 构建文件 | 从代码推断，标 `[推断]` |
| 项目简介 - 业务背景 | README、package.json description | **整块写"待补充"**，不要脑补 |
| 技术栈总览 | 依赖清单分类 | 找不到的类别省略 |
| 核心功能列表 | 各域 Controller 端点（Step 4.5） | 命名歧义标 `[推断]`；都推不出写"待补充" |
| 核心领域模型 | 实体类代码 + 注解 | 字段级：略过无法确认的字段；实体级：无法确认则降级到"次要实体"表 |
| 业务流程 | Controller + Service 调用链 | 只画能追踪的部分，标 `[部分流程未覆盖]` |
| 项目结构 | 目录扫描 | 客观陈述 |
| 系统架构图 | Dockerfile / compose / 依赖 / 配置 | 推不出的节点不画；推不出的连线虚线 + `[待补充]` |
| 里程碑 - 历史 | git tag + CHANGELOG | 两者都无时整块写"待补充" |
| 里程碑 - 未来 | — | 整块写"待补充（需人工规划）" |
| 外部依赖 | 构建 + 配置文件 | 无则不列 |
| 部署 - 环境要求 | 构建文件、Dockerfile、compose、CI | 未声明组件写 `待补充` |
| 部署 - 启动步骤 | README、Makefile、scripts、CMD、CI | 找不到写 `待补充（未发现启动脚本）` |
| 部署 - 配置说明 | `application-example.yml`、`.env.example`、配置类 | 不要编造配置项 |
| 开发指南 | CONTRIBUTING、lint 配置、git hooks、CODEOWNERS | 找不到整节写 `待补充` |

### 7.2 判断每个域是单文件还是拆分模式

**拆分触发**（见输出路径规范）：任一条件命中（实体 ≥ 4、流程 ≥ 3、预估 > 400 行）即拆。

**为什么设阈值**：小域拆成 3 个空文件比一个简洁 README 更难读；大域塞进一个文件又让人滚屏找不到。阈值让文档密度自适应。

### 7.3 数据到文件的分发

下表定义 Step 1-6 产出去哪个文件。首次和增量模式都用这个分发表；两种模式的差异在 7.4 / 7.5 的写入方式。

**项目层** `docs/wiki/`（6 个文件，直接放根目录）：

| 文件 | 内容 | 来源 |
|------|------|------|
| `README.md` | 项目简介（背景/技术栈/目标用户）+ 核心功能 + 域索引 | Step 1 + 4.5 |
| `architecture.md` | 架构模式 + 系统架构图 + 目录结构 + 领域划分 + 跨域 ER | Step 5 |
| `milestones.md` | 历史里程碑 + 未来规划 | Step 1.4 |
| `dependencies.md` | 依赖表格、第三方服务 | Step 6 |
| `deployment.md` | 环境、配置、启动 | 7.1 |
| `development.md` | 本地开发、代码规范、提交规范、FAQ | 7.1 |

**领域层** `docs/wiki/domains/`：

| 文件 | 内容 |
|------|------|
| `domains/README.md` | 领域清单（表格：域名 / 职责 / 核心实体 / 文档链接） |
| `domains/<X>/README.md`（单文件） | 概览 + 对外接口 + 实体 + 流程 |
| `domains/<X>/README.md`（拆分） | 概览 + 对外接口 + 实现位置 + 跳转段到 domain-model.md / flows.md |
| `domains/<X>/domain-model.md`（拆分） | 本域所有实体 |
| `domains/<X>/flows.md`（拆分） | 本域所有流程 + 状态机 |
| `domains/<X>/api.md`（可选，API ≥ 20） | 完整 API 清单 |

**章节间互链**：
- `docs/wiki/README.md` 目录链接到同级其他文件 + `./domains/README.md`
- 每个 `domains/<x>/` 下文件头部加：`回到：[领域清单](../README.md) · [项目总览](../../README.md)`
- **所有跨域引用统一用 `../<other-domain>/README.md#xxx`**（见全局原则-跨域链接）

### 7.4 写入：首次模式

```bash
mkdir -p docs/wiki
mkdir -p docs/wiki/domains
# 对每个域：
mkdir -p docs/wiki/domains/<domain>
```

按 `references/output-templates.md` 的骨架逐文件 `Write`，所有模板里的 `<!-- auto:xxx -->...<!-- /auto:xxx -->` 标记**原样保留**——它们是下次增量跑的定位锚点。

**单领域退化**（Step 2.3 用户确认后）：`docs/wiki/` 下直接 `README.md` + `domain-model.md` + `flows.md`，不创建 `domains/`。

### 7.5 写入：增量模式（仅在 `docs/wiki/` 已存在时）

对每个**既有**目标文件执行以下合并流程（新增的文件按 7.4 首次模式写）：

#### 流程

1. **Read 既有文件**
2. **定位所有 auto 块**：用正则 `<!-- auto:([^\s>]+) -->([\s\S]*?)<!-- /auto:\1 -->` 抽出 `id` 和现有内容。`[^\s>]+` 允许中文 ID（如 `auto:flow:创建订单流程`）
3. **对每个既有 auto 块**：
   - 从 Step 1-6 的分析结果算出该 id 对应的新内容
   - **幂等跳过**：若新内容与既有内容 byte-equal，**不调用 `Edit`**——代码没变时不必写入，既减少 diff 噪音，也让 Step 8.6 的 mtime 检查有意义
   - 否则用 `Edit` 把旧块整体替换为新块（保留开闭标记本身）
   - 若新内容为空（代码里已删除对应实体/流程）→ 块内留一行 `<!-- 代码中未发现此项 -->`，**不删标记、不碰周围 prose**
   - 若 id 是 `auto:domains-table` → **不执行本步骤**，按下方"新领域"小节处理
4. **处理代码里有但文档里没有的新项**：按模板生成新 auto 块（含标记和相邻的人工小节占位），追加到合理位置：
   - 新实体 → 追加到对应域文件的"核心实体"小节末尾（单文件模式 = `domains/<x>/README.md`；拆分模式 = `domains/<x>/domain-model.md`）
   - 新流程 → 追加到"主要流程"小节末尾（单文件 = `README.md`；拆分 = `flows.md`）
   - 新依赖类别 → 追加到 `dependencies.md` 对应小节
   - 新核心功能 → 追加到 `docs/wiki/README.md` 的 `auto:features` 块内
5. **人工层完全不动**：标记外的所有 prose、"业务背景 / 例外"、"设计说明 / 例外"、已填写的"待补充"、项目层 README 的业务背景/目标用户/核心价值小节等，原样透传

#### 新领域（domain 级别的新增）

Step 2 识别到的"待归属"路径（不在既有 `auto:domains-table` 任何 path 下）：

- 在 `auto:domains-table` 块内追加一行 `| 待归属 | <path> | - | 建议归属：<域>（AI 推断） |`
- **不自动新建 `docs/wiki/domains/<new>/` 目录**——等用户确认归属后下次重跑 skill 再建
- 这避免了在归属未定时预先铺开文件结构

`auto:domains-table` 其余处理规则（既有行不重排、不删）同执行模式节的说明。

#### 整体人工文件说明

`deployment.md` 和 `development.md` 整体是人工层（大部分是团队规范 prose），未加 auto 标记。增量模式下这两个文件**完全不动**。首次模式按模板生成"待补充"占位，由用户填写后永久保留。

### 7.6 生成摘要

给用户一段简短摘要：

- 模式：首次 / 增量
- 增量模式下：新增了哪些实体/流程/依赖（列清单），哪些 auto 块变空了（候选已删除），有没有"待归属"的新路径
- 首次模式下：核心功能、技术栈、域数量及名称、每域实体/流程数量
- 文档保存位置
- 手动调整建议（"如需修改领域划分，直接编辑 `architecture.md` 的 `auto:domains-table` 块"）

---

## Step 8: 输出质量自检

生成后执行自检。**前两项必须实际执行工具调用验证，不能仅目测。**

### 8.1 来源真实性抽查

防止 AI 为了格式好看而编造行号 / 文件路径。

1. 从各 `domains/<x>/` 文档中随机抽 **5 条 `来源: xxx.java:45` 形式的引用**
2. 对每条：
   - Glob / Read 确认文件存在
   - Read 读取行号附近代码（±5 行），确认与说明匹配
3. 发现失实 → 改为"待补充（需人工确认）"；抽查不再继续补判（避免死循环）

### 8.2 实体字段真实性抽查

1. 随机抽 **3 个实体的字段清单**
2. Read 打开源文件对比字段名、类型、注解
3. 虚构字段 → 删除；字段缺失 → 补齐

### 8.3 结构完整性

- `docs/wiki/` 下 6 个项目层文件都存在（README、architecture、milestones、dependencies、deployment、development）
- 多领域：`docs/wiki/domains/README.md` + 每个 `docs/wiki/domains/<X>/README.md` 存在
- 单领域退化：`docs/wiki/` 下 `README.md` + `domain-model.md` + `flows.md` 存在

### 8.4 链接抽查

- `docs/wiki/README.md` 的目录链接指向的文件都存在
- 跨域引用（`../<other-domain>/README.md#xxx`）随机抽 3 条：目标文件存在且锚点存在
- 所有跨域链接都指向 `README.md`（不是 `domain-model.md` / `flows.md`）

### 8.5 内容质量

- 没有出现 `output-templates.md` 中的示例值被当作项目事实写入
- 所有 Mermaid 图语法正确（参与者/状态/关系名无错字）
- 单域核心实体 ≤ 10、主要流程 ≤ 5；超出已移入表格
- 跨域 ER 主图只画跨域引用，不含域内细节

### 8.6 增量模式专属自检

仅在本次执行走增量路径时跑：

- 随机抽 **3 处标记外的人工 prose**（如填过的"业务背景"、"设计说明"小节），对比 Step 7 前 Read 到的原文——必须逐字一致，证明没有误伤人工层
- 随机抽 **2 个 auto 块**，确认开闭标记都完整保留，块外文本未被吞掉
- `auto:domains-table` 既有行数 ≥ 上次读取时的行数（只增不减，增量只发生在"待归属"行）
- `deployment.md` 和 `development.md` 未被修改（mtime 未变 或 内容 diff 为空）

---

## 分析技巧

### 代码推断

信息不完整时从代码推断，但标 `[推断]`：
- **项目用途**：从 Controller 端点名称推断
- **业务规则**：从 Service 层验证逻辑推断
- **数据关系**：从 ORM 注解或 SQL 查询推断
- **集成服务**：从配置文件 key 名推断

### 高效分析工具

1. **语义级探索**（Claude Code: `Agent` + `subagent_type=Explore`）——开放问题，如 "Where are entity classes?" / "How is auth implemented?"
2. **内容搜索**（`Grep`）：`@Entity`、`@RestController`、`@Transactional`
3. **文件名模式**（`Glob`）：`**/*Controller.java`、`**/entity/*.java`

### 处理大型项目

按非依赖源文件数分档：

| 规模 | 策略 |
|------|------|
| < 100 文件 | 常规流程 |
| 100-500 文件 | 采样分析 + 严格核心筛选（Step 3.3 / 4.2 的上限） |
| 500-2000 文件 | 并行派发子 agent 分模块分析 |
| > 2000 文件 | 并行 + 分批写入（见下"context 管理"） |

**并行派发**（Claude Code 用 `Agent`；无并行能力则见下）：

```
子任务 1: 用户模块（entity/User*, service/User*, controller/User*）
子任务 2: 订单模块（entity/Order*, service/Order*, controller/Order*）
子任务 3: 支付模块（entity/Payment*, service/Payment*, client/*Pay*）
```

每子任务输出结构化结果（实体片段 + 流程片段），主 agent 汇总去重。

**无并行时的 context 管理**：

1. 每批 ≤ 20 个文件，读完立即提炼结构化摘要（实体名 + 字段 + 方法签名），**不保留原始源码**
2. 每分析完一个模块立即写入对应文件，清除该模块源码 context
3. 优先 Grep 统计匹配数量，需要详细内容时才 Read
4. 单次会话不够时提示用户："已完成 [模块 A, B]，请新会话继续"

Monorepo 处理详见 language-hints.md 的 "Monorepo / 多模块项目" 小节。

---

## 最佳实践

1. **保持客观**：基于代码事实，避免主观评价
2. **使用图表**：复杂关系用 Mermaid
3. **提供上下文**：不仅"是什么"，还要"为什么"（从注释或 commit 提取）
4. **标注来源**：重要信息标来源文件
5. **宁缺毋滥**：找不到来源写"待补充"，不要用示例值填充
