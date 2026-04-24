# 输出格式模板

本文件集中存放 `SKILL.md` Step 7 组装阶段的 markdown 骨架。

> ⚠️ 所有示例中的具体值（项目名、字段名、版本号、业务规则）**仅为格式示意**，必须替换为从当前项目实际读取到的内容。找不到来源写 `待补充（需人工确认）`。

> ⚠️ **跨域链接统一用 `../<other-domain>/README.md#<anchor>`**（见 SKILL.md 全局原则-跨域链接）。拆分模式下 `README.md` 需保留实体/流程跳转段，让锚点始终可达。

## auto 标记约定（增量更新的关键）

模板里用 HTML 注释 `<!-- auto:<type>[:<name>] -->` ... `<!-- /auto:<type>[:<name>] -->` 包裹**代码可重算的原子区块**。渲染后不可见，对 skill 是明确的写入边界。

**规则**：
- **标记内**的内容：skill 每次跑都会从代码重新生成并**完整替换**。不要在标记内手写注释或调整——会被覆盖
- **标记外**的内容（prose、人工补充的业务背景、例外说明等）：skill **永不改写**，原样保留
- 新实体/新流程：skill 在合适位置追加新的 auto 块
- 代码里删掉的项：对应 auto 块内容变空，**不删标记本身、不删周围 prose**——让你看到空块时自己决定如何处理

**标记清单**（出现位置见下方各模板）：

| 标记 | 包裹内容 |
|------|---------|
| `auto:project-meta` | 项目类型、版本、构建工具 |
| `auto:tech-stack` | 技术栈总览 |
| `auto:features` | 核心功能清单 |
| `auto:domain-index` | 项目层 README 的业务域表格（跟随 `auto:domains-table` 的域名重算） |
| `auto:domains-listing` | 领域层 `domains/README.md` 的领域清单表（跟随 `auto:domains-table` 的域名重算） |
| `auto:arch-pattern` | 架构模式判断 |
| `auto:arch-diagram` | 系统架构图 + 组件清单 |
| `auto:dir-tree` | 目录结构 |
| `auto:er-diagram` | 跨域 ER 主图 |
| `auto:deps:<类别>` | 依赖分类表格 |
| `auto:entity:<Name>` | 单个实体的字段、关联、代码中的业务规则 |
| `auto:flow:<Name>` | 单个流程的序列图、关键步骤 |
| `auto:state:<Entity>` | 单个状态机图 |
| `auto:endpoints` | 端点表格 |
| `auto:domains-table` | 01-architecture.md 的领域划分表（**混合区**：首次填入；之后**行级既有权威**——既有行的任何单元格、备注都视为人工权威，skill 永不覆写；只在发现未归属的新路径时**追加**"待归属"行） |

**人工专属小节**（永不在 auto 标记内，skill 不动）：
- 业务背景 / 目标用户 / 核心价值
- 每个实体下的"业务背景 / 例外"小节
- 每个流程下的"设计说明 / 例外"小节
- 未来里程碑规划

---

## 项目层

### `docs/wiki/README.md`（入口）

```markdown
# [项目名称] - 项目概览

> 生成时间: [当前日期]
> 代码版本: [Git commit 短 hash 12 位，非 git 填 none]

## 项目简介

<!-- auto:project-meta -->
- **项目类型**: [Web 应用 / 微服务 / 库 / CLI 工具等]
- **版本**: [当前版本]（来源: [构建文件]）
- **构建工具**: [Maven / Gradle / npm / pnpm / cargo 等]
<!-- /auto:project-meta -->

### 业务背景

> 👤 人工小节（skill 不改写）。首次生成若读不到，保留下方"待补充"提示。

[从 README 引言 / package.json description 读取；读不到时保留下方占位]

> ⚠️ 待补充（需人工确认）：项目的业务背景、要解决的问题

### 目标用户 / 使用场景

> 👤 人工小节（skill 不改写）。

[从 README 的 "Who is this for" / "Use cases" / 权限角色推断]

> ⚠️ 待补充（需人工确认）：项目面向的用户角色和典型使用场景

### 核心价值

> 👤 人工小节（skill 不改写）。

[从 README 的 Features / Why 节推断]

> ⚠️ 待补充（需人工确认）：项目的核心价值主张

## 技术栈总览

> 高层分类清单，版本详情见 [外部依赖](./03-dependencies.md)。找不到的类别省略不写。

<!-- auto:tech-stack -->
- **后端**: Spring Boot 3.x（来源: `pom.xml`）
- **前端**: React 18 / Next.js 14（来源: `web/package.json`）
- **数据存储**: MySQL 8, Redis 7（来源: 依赖 + `application.yml`）
- **消息队列**: Kafka（来源: `spring-kafka` 依赖）
- **DevOps**: Docker, GitHub Actions（来源: `Dockerfile`, `.github/workflows/`）
<!-- /auto:tech-stack -->

## 核心功能

> 用户视角的核心功能清单。完整端点见各域 README。

<!-- auto:features -->
### 订单相关
- [下单](./domains/order/README.md#创建订单流程) — POST /api/orders
- [查询订单](./domains/order/README.md) — GET /api/orders/{id}
- [取消订单](./domains/order/README.md) — POST /api/orders/{id}/cancel

### 支付相关
- [在线支付](./domains/payment/README.md#charge) — POST /api/payments
- [申请退款](./domains/payment/README.md#refund) — POST /api/refunds

### 账户相关
- [用户注册](./domains/user/README.md#注册流程)
- [登录](./domains/user/README.md#登录流程)
<!-- /auto:features -->

[按域分组，每组 3-5 个；全量 ≤ 20 个；命名歧义标 [推断]]

## 业务域

<!-- auto:domain-index -->
| 域 | 职责 | 核心实体 | 文档 |
|----|------|---------|------|
| order | 订单创建、状态流转 | Order, OrderItem | [./domains/order/](./domains/order/README.md) |
| payment | 支付受理、退款 | Payment, Refund | [./domains/payment/](./domains/payment/README.md) |
| user | 账户管理、认证 | User, UserProfile | [./domains/user/README.md](./domains/user/README.md) |
<!-- /auto:domain-index -->

完整清单：[领域索引](./domains/README.md)

## 文档目录

**项目层**（本目录）：
- [项目结构](./01-architecture.md) — 架构模式、系统架构图、目录组织、领域划分、跨域 ER
- [里程碑](./02-milestones.md) — 发布历史与未来规划
- [外部依赖](./03-dependencies.md) — 框架、库、第三方服务
- [部署说明](./04-deployment.md) — 环境要求、启动步骤
- [开发指南](./05-development.md) — 本地开发、代码规范

**领域层**：
- [领域清单](./domains/README.md) — 所有业务域索引

## 文档维护

本文档由 AI 自动生成。重跑 skill 时采用**增量更新**：

- `<!-- auto:xxx -->` 标记内的内容会从代码重新生成（技术栈、功能清单、实体字段等）
- 标记外的 prose 和"业务背景"等 👤 人工小节**永不改写**
- 新增的实体/流程会追加，代码里删除的项 auto 块内容变空（由人工决定清理）

**需人工补充**（AI 无法推断）：
- 业务背景和决策原因
- 架构演进历史
- 性能指标与优化建议

**修改领域划分**：编辑 `01-architecture.md` 的"领域划分"表即可——重跑时 skill 以既有表为准，只在发现未归属的新代码路径时追加到"待归属"行。
```

---

### `docs/wiki/01-architecture.md`

```markdown
# 项目结构

[返回概览](./README.md)

## 架构模式

<!-- auto:arch-pattern -->
本项目采用 **[分层架构 / 六边形 / 微服务 / 模块化单体]** 模式。
**判断依据**: [目录结构 / 包命名 / 关键注解]
<!-- /auto:arch-pattern -->

## 系统架构图

> 展示部署拓扑和组件关系。推不出的节点不画，推不出的连线用虚线 + `[待补充]`。

<!-- auto:arch-diagram -->
\`\`\`mermaid
flowchart TB
    User[终端用户]
    Admin[管理员]

    subgraph Frontend[前端]
        Web[Web App<br/>Next.js]
        AdminUI[管理后台]
    end

    subgraph Backend[后端服务]
        API[API Server<br/>Spring Boot]
    end

    subgraph Data[数据层]
        MySQL[(MySQL)]
        Redis[(Redis)]
    end

    subgraph MQ[消息层]
        Kafka[Kafka]
    end

    subgraph External[第三方]
        Alipay[支付宝]
        OSS[对象存储]
    end

    User --> Web
    Admin --> AdminUI
    Web --> API
    AdminUI --> API
    API --> MySQL
    API --> Redis
    API --> Kafka
    API --> Alipay
    API --> OSS
\`\`\`

### 组件清单

| 组件 | 实际证据 | 备注 |
|------|---------|------|
| MySQL | `mysql-connector-j` 依赖 + `spring.datasource.url` in `application.yml` | |
| Redis | `lettuce-core` 依赖 + `spring.data.redis.*` 配置 | |
| Kafka | `spring-kafka` 依赖 + `spring.kafka.bootstrap-servers` 配置 | |
| 支付宝 SDK | `alipay-sdk-java` 依赖 + `AlipayClient` 使用 | |
| OSS | `aliyun-sdk-oss` 依赖 | |
| Nginx / API 网关 | `> ⚠️ 待补充（需人工确认）`：未在代码库发现，通常在部署层 | |
<!-- /auto:arch-diagram -->

## 目录结构

<!-- auto:dir-tree -->
\`\`\`
[使用 Glob 扫描得到的真实目录树，按语言自适应深度]
\`\`\`
<!-- /auto:dir-tree -->

## 领域划分

> 特殊区块：首次生成时由 AI 填入；之后**以此表为权威**，skill 重跑时会读取此表作为归属依据。用户想调整划分直接改此表 + 对应目录即可。

<!-- auto:domains-table -->
| 域 | paths | 核心实体（归属本域）| 职责 |
|----|-------|---------------------|------|
| order | `src/main/java/com/xxx/order/**` | Order, OrderItem | 订单创建、状态流转 |
| payment | `src/main/java/com/xxx/payment/**` | Payment, Refund | 支付受理、退款 |
| user | `src/main/java/com/xxx/user/**` | User, UserProfile | 账户管理、认证 |
<!-- /auto:domains-table -->

> **共享基础设施**（shared-lib、util 等）：[说明位置，如 `packages/common/**`]——不作为业务域。

### 跨域 ER 主图

> 只展示**跨域引用**的实体关系，域内细节请看各域的 `domain-model.md`（或单文件模式下的 `README.md`）。

<!-- auto:er-diagram -->
\`\`\`mermaid
erDiagram
    User ||--o{ Order : "placed by (referenced by order)"
    User ||--o{ Payment : "paid by (referenced by payment)"
\`\`\`
<!-- /auto:er-diagram -->

## 模块说明

### [层次/模块名]
- **职责**: [从代码读取的真实职责]
- **规范**（从代码归纳）: [注解使用、返回类型等]

[继续描述其他层次]
```

---

### `docs/wiki/02-milestones.md`

```markdown
# 项目里程碑

[返回概览](./README.md)

> 历史里程碑从 `git tag` + `CHANGELOG.md` 提取；未来规划需人工填写。

## 历史里程碑

\`\`\`mermaid
timeline
    title 项目演进
    2024-06 : v0.1.0<br/>初版上线
    2024-09 : v0.5.0<br/>接入支付网关
    2024-12 : v1.0.0<br/>正式发布
\`\`\`

### 发布历史

| 版本 | 日期 | 主要变更 | 来源 |
|------|------|---------|------|
| v0.1.0 | 2024-06-10 | 初版上线 | git tag + CHANGELOG.md |
| v1.0.0 | 2024-12-15 | 正式发布 | CHANGELOG.md |

[无 git tag 也无 CHANGELOG 时整节改为：]

> ⚠️ 待补充（需人工确认）：未发现 git tag 或 CHANGELOG.md，请手动补充历史里程碑

## 未来规划

> ⚠️ 待补充（需人工确认）：未来里程碑需人工规划填写。建议列出：
> - 下一个版本的目标（功能 / 时间）
> - 中期（3-6 个月）的主要方向
> - 长期愿景或技术债务偿还计划
```

---

### `docs/wiki/03-dependencies.md`

```markdown
# 外部依赖

[返回概览](./README.md)

## 核心框架依赖

<!-- auto:deps:core-framework -->
| 依赖 | 版本 | 用途 |
|------|------|------|
| [框架名] | [版本] | [用途] |
<!-- /auto:deps:core-framework -->

## 数据存储

<!-- auto:deps:data-store -->
| 技术 | 版本 | 用途 |
|------|------|------|
| [数据库] | [版本] | [用途]（来源: 配置文件） |
<!-- /auto:deps:data-store -->

## 第三方服务

<!-- auto:deps:external-services -->
### [服务名]
- **用途**: [用途]
- **配置**: [配置文件位置和 key 前缀]
- **使用位置**: [调用代码文件]
<!-- /auto:deps:external-services -->

## 工具库

<!-- auto:deps:utility -->
| 依赖 | 版本 | 用途 |
|------|------|------|
<!-- /auto:deps:utility -->

## 开发和测试

<!-- auto:deps:dev-test -->
| 依赖 | 版本 | 用途 |
|------|------|------|
<!-- /auto:deps:dev-test -->
```

---

### `docs/wiki/04-deployment.md`

```markdown
# 部署说明

[返回概览](./README.md)

> 以下内容基于项目中的构建文件、Dockerfile、CI 配置和 README 提取。未找到来源的条目标注为「待补充（需人工确认）」。

## 环境要求
- [语言 + 版本]（来源: [pom.xml / package.json engines / go.mod 等]）
- [数据库 + 版本]（来源: [docker-compose.yml / README / 配置文件]）
- [其他必需组件]

## 配置说明
<!-- 仅列出代码库中真实存在的 example/.env.example 里的配置项 -->
1. ...

## 启动步骤
<!-- 来源: README / Makefile / package.json scripts / Dockerfile CMD -->

\`\`\`bash
[从代码库读取到的实际命令]
\`\`\`
```

---

### `docs/wiki/05-development.md`

```markdown
# 开发指南

[返回概览](./README.md)

> ⚠️ 本节多为团队规范，代码库中通常不完整。只写能从 CONTRIBUTING.md、lint 配置、git hooks、CI 等读出的事实，其余写「待补充（需人工确认）」。

## 本地开发环境搭建
[从 README / CONTRIBUTING.md 读取；无则: 待补充]

## 代码规范
[从 .editorconfig / .eslintrc / .prettierrc / checkstyle.xml 读取；无则: 待补充]

## 提交规范
[从 commitlint.config / .gitmessage / CONTRIBUTING.md 读取；无则: 待补充]

## 常见问题
[从 README FAQ 章节读取；无则: 待补充]
```

---

## 领域层

### `docs/wiki/domains/README.md`（领域清单）

```markdown
# 业务域清单

[返回项目总览](../README.md)

> 每个域自包含：实体、流程、API 都在各自目录。跨域实体引用通过链接指向归属域（如 Order 引用 User 时链接到 user 域的 README.md）。

<!-- auto:domains-listing -->
| 域 | 职责 | 核心实体 | 入口 | 文档 |
|----|------|---------|------|------|
| order | 订单创建、状态流转 | Order, OrderItem | `OrderController` | [./order/](./order/README.md) |
| payment | 支付受理、退款 | Payment, Refund | `PaymentController` | [./payment/](./payment/README.md) |
<!-- /auto:domains-listing -->
```

---

### `docs/wiki/domains/<X>/README.md`（单文件模式）

小域默认模板（实体 < 4 个、流程 < 3 个、总量预估 < 400 行）。

```markdown
# Order 领域

[返回项目总览](../../README.md) · [返回领域清单](../README.md)

## 领域职责
订单的创建、状态流转、查询与取消。

## 对外接口

<!-- auto:endpoints -->
**REST API**（来源: `OrderController.java`）:
- `POST /api/orders` — 创建订单
- `GET /api/orders/{id}` — 查询订单
- `POST /api/orders/{id}/cancel` — 取消订单

**事件**（来源: `OrderEventPublisher.java`）:
- 发布：`OrderCreated`、`OrderCancelled`
- 订阅：`PaymentCompleted`（来自 payment 域）
<!-- /auto:endpoints -->

## 核心实体

### Order (订单)

<!-- auto:entity:Order -->
- **来源文件**: `order/entity/Order.java`
- **关键字段**:
  - `id`: 订单 ID
  - `userId`: 下单用户（引用 [User](../user/README.md#user)，归属 user 域）
  - `status`: 订单状态（见下方状态机）
  - `totalAmount`: 订单总额
- **关联关系**:
  - 一对多：`OrderItem`（`@OneToMany`）
  - 多对一：`User`（跨域引用）
- **代码中的业务规则**（从校验/调度/状态机代码提取）:
  - 创建后 30 分钟未支付自动取消（来源: `OrderScheduler.java:23`）
  - 状态只能按状态机定义的边迁移（来源: `OrderService.transitionTo`）
<!-- /auto:entity:Order -->

**业务背景 / 例外情况**（👤 人工补充，skill 不改写）:

> ⚠️ 待补充（需人工确认）：填写此实体的业务背景、为什么这样设计、代码里推不出的例外规则。

### OrderItem (订单项)

<!-- auto:entity:OrderItem -->
[同上格式；字段、关联、代码可验证规则]
<!-- /auto:entity:OrderItem -->

## 主要流程

### 创建订单流程（单域）

<!-- auto:flow:创建订单流程 -->
**入口**: `OrderController.create()` (POST /api/orders)

\`\`\`mermaid
sequenceDiagram
    participant Client
    participant OrderController
    participant OrderService
    participant OrderRepository

    Client->>OrderController: POST /api/orders
    OrderController->>OrderService: createOrder(dto)
    OrderService->>OrderRepository: save(order)
    OrderRepository-->>OrderService: Order
    OrderService-->>Client: 201 Created
\`\`\`

**关键步骤**（仅记录代码中可追踪的逻辑）:
1. 参数校验（来源: `@Valid`）
2. 库存扣减（来源: `InventoryService.deduct`）
<!-- /auto:flow:创建订单流程 -->

**设计说明 / 例外**（👤 人工补充，skill 不改写）:

> ⚠️ 待补充：性能目标、已知边界情况、运营上的例外处理。

### 下单支付流程（跨域，归属本域）

<!-- auto:flow:下单支付流程 -->
**入口**: `OrderController.createAndPay()` (POST /api/orders/pay)
**涉及其他域**: payment

\`\`\`mermaid
sequenceDiagram
    participant Client
    participant OrderService
    participant PaymentService as PaymentService<br/>[payment 域]
    participant PaymentGateway

    Client->>OrderService: POST /api/orders/pay
    OrderService->>PaymentService: charge(amount)
    Note right of PaymentService: 详见 ../payment/README.md#charge
    PaymentService->>PaymentGateway: 第三方调用
    PaymentGateway-->>PaymentService: 结果
    PaymentService-->>OrderService: Payment 状态
    OrderService-->>Client: Order + Payment
\`\`\`

**关键步骤**:
1. 订单与支付**同一事务**（来源: `OrderService.java:78` `@Transactional`）
2. 调用 [PaymentService.charge](../payment/README.md#charge) 完成扣款
3. 支付失败回滚订单
<!-- /auto:flow:下单支付流程 -->

[对本域每个主要流程重复，上限 5 个]

## 状态机（如有）

### Order 状态机

<!-- auto:state:Order -->
**来源**: `order/entity/OrderStatus.java` + `OrderService.transitionTo`

\`\`\`mermaid
stateDiagram-v2
    [*] --> PENDING: 创建
    PENDING --> PAID: 支付成功
    PENDING --> CANCELLED: 超时/取消
\`\`\`
<!-- /auto:state:Order -->

## 实现位置

<!-- auto:impl-locations -->
- Controller: `order/controller/`
- Service: `order/service/`
- Repository: `order/repository/`
- Entity: `order/entity/`
<!-- /auto:impl-locations -->

## 其他端点

<!-- auto:endpoints:secondary -->
| 方法 | 端点 | 入口 | 简述 |
|------|------|------|------|
| GET | `/api/orders` | `OrderController.list` | 订单列表分页 |
<!-- /auto:endpoints:secondary -->
```

---

### `docs/wiki/domains/<X>/` 拆分模式

触发条件：实体 ≥ 4 或流程 ≥ 3 或预估 > 400 行。

**`<X>/README.md`**（拆分模式的概览 + 跳转段，让跨域锚点可达）

```markdown
# Order 领域

[返回项目总览](../../README.md) · [返回领域清单](../README.md)

## 领域职责
订单的创建、状态流转、查询与取消。

## 对外接口

<!-- auto:endpoints -->
**REST API**（来源: `OrderController.java`）:
- `POST /api/orders` — 创建订单
- [完整列表略，见本域 Controller]

**事件**（来源: `OrderEventPublisher.java`）:
- 发布：`OrderCreated`、`OrderCancelled`
<!-- /auto:endpoints -->

## 实现位置

<!-- auto:impl-locations -->
- Controller: `order/controller/`
- Service: `order/service/`
- Repository: `order/repository/`
- Entity: `order/entity/`
<!-- /auto:impl-locations -->

## 核心实体

> 跨域链接的锚点保留在此处，详细说明见 `domain-model.md`。

### Order
订单主实体。详见 [domain-model.md#order](./domain-model.md#order)。

### OrderItem
订单项。详见 [domain-model.md#orderitem](./domain-model.md#orderitem)。

## 主要流程

> 跨域链接的锚点保留在此处，详细说明见 `flows.md`。

### 创建订单流程
详见 [flows.md#创建订单流程](./flows.md#创建订单流程)。

### 下单支付流程
详见 [flows.md#下单支付流程](./flows.md#下单支付流程)。

## 章节

- [领域模型](./domain-model.md) — 本域实体、关系、业务规则
- [业务流程](./flows.md) — 本域流程、状态机、端点清单
```

**`<X>/domain-model.md`**

```markdown
# Order 领域模型

[返回 Order 领域](./README.md) · [领域清单](../README.md) · [项目总览](../../README.md)

## 实体关系图（本域）

<!-- auto:er-diagram:domain -->
\`\`\`mermaid
erDiagram
    Order ||--|{ OrderItem : contains
    Order }o--|| User : "placed by (ref user 域)"
\`\`\`
<!-- /auto:er-diagram:domain -->

> 跨域引用（如 User）只画关系线，实体详情见归属域。

## 核心实体

### Order (订单)

<!-- auto:entity:Order -->
[字段、关联、代码可验证规则]
<!-- /auto:entity:Order -->

**业务背景 / 例外情况**（👤 人工补充）:

> ⚠️ 待补充。

## 次要实体

<!-- auto:entities:secondary -->
| 实体 | 用途 | 来源文件 |
|------|------|---------|
| ... | ... | ... |
<!-- /auto:entities:secondary -->
```

**`<X>/flows.md`**

```markdown
# Order 业务流程

[返回 Order 领域](./README.md) · [领域清单](../README.md) · [项目总览](../../README.md)

## 主要流程

### 创建订单流程

<!-- auto:flow:创建订单流程 -->
[序列图 + 关键步骤；跨域流程按归属规则放在归属域]
<!-- /auto:flow:创建订单流程 -->

**设计说明 / 例外**（👤 人工补充）:

> ⚠️ 待补充。

## 状态机

### Order 状态机

<!-- auto:state:Order -->
[状态机图]
<!-- /auto:state:Order -->

## 其他端点

<!-- auto:endpoints:secondary -->
| 方法 | 端点 | 入口 | 简述 |
|------|------|------|------|
<!-- /auto:endpoints:secondary -->
```

---

## 单领域退化结构

Step 2.3 用户确认后使用。直接在 `docs/wiki/` 下：

```
docs/wiki/
├── README.md              # 项目概览 + 核心功能 + 技术栈 + 链接到下面两个
├── domain-model.md        # 所有实体
└── flows.md               # 所有流程 + 状态机
```

此时项目层的架构/部署/依赖/开发等内容合并进 `docs/wiki/README.md` 适当小节，不再拆多个文件。
