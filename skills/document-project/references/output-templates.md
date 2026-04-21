# 输出格式模板

本文件集中存放 `SKILL.md` 中各 Step 的 markdown 输出样板。当你在执行对应步骤需要具体格式时，加载本文件查阅。

> ⚠️ 所有示例中的具体值（项目名、字段名、版本号、业务规则）**仅为格式示意**，必须替换为从当前项目实际读取到的内容。找不到来源的条目写 `待补充（需人工确认）`。

---

## Step 1 输出模板：项目简介

```markdown
# [项目名称]

## 项目简介
- **项目类型**: [Web应用 / 微服务 / 库 / CLI 工具等]
- **技术栈**: [主要技术栈，来源: 构建文件]
- **版本**: [当前版本，来源: 构建文件]
- **构建工具**: [Maven / Gradle / npm / pnpm / cargo 等]

## 项目目标
[从 README 或代码推断的项目目标和用途。若纯推断，标注 [推断]]
```

---

## Step 2 输出模板：核心领域模型

```markdown
## 核心领域模型

### 实体关系图
\`\`\`mermaid
erDiagram
    User ||--o{ Order : places
    Order ||--|{ OrderItem : contains
    Product ||--o{ OrderItem : "ordered in"
\`\`\`

### 核心实体

#### User (用户)
- **用途**: 系统用户账户管理
- **来源文件**: `entity/User.java`
- **关键字段**:
  - `id`: 用户唯一标识
  - `username`: 用户名
  - `email`: 邮箱地址
  - `role`: 用户角色（ADMIN/USER）
- **业务规则**（仅列出代码中可验证的规则）:
  - 用户名必须唯一（来源: `@Column(unique = true)`）
  - 邮箱需要验证（来源: `EmailVerificationService` 调用）
- **关联关系**:
  - 一个用户可以有多个订单（`@OneToMany`）

[对每个核心实体重复此格式]
```

---

## Step 3 输出模板：业务流程

```markdown
## 业务流程

### 用户注册流程
**入口**: `AuthController.register()` (POST /api/register)

\`\`\`mermaid
sequenceDiagram
    participant Client
    participant AuthController
    participant UserService
    participant UserRepository
    participant EmailService

    Client->>AuthController: POST /api/register
    AuthController->>UserService: registerUser(dto)
    UserService->>UserRepository: findByEmail(email)
    UserRepository-->>UserService: null
    UserService->>UserRepository: save(user)
    UserService->>EmailService: sendVerificationEmail(user)
    EmailService-->>UserService: success
    UserService-->>AuthController: UserDTO
    AuthController-->>Client: 201 Created
\`\`\`

**关键步骤说明**（仅记录代码中可追踪的逻辑）:
1. **邮箱唯一性检查**: 来源 `UserService.java:45`
2. **密码加密**: 使用 BCrypt，来源 `UserService.java:52`
3. **发送验证邮件**: 异步，来源 `@Async` 注解
4. **事务管理**: `@Transactional` 范围为整个方法

**异常处理**（来源: `GlobalExceptionHandler` 及方法签名）:
- `EmailAlreadyExistsException`: 邮箱已被注册
- `EmailSendFailureException`: 邮件发送失败（记录日志但不回滚）

[对每个主要业务流程重复此格式]
```

---

## Step 4 输出模板：项目结构

```markdown
## 项目结构

### 架构模式
本项目采用 **[分层架构 / 六边形 / 微服务 / 模块化单体]** 模式。
判断依据: [目录结构 / 包命名 / 关键注解]

### 目录结构
\`\`\`
[使用 Glob 扫描得到的真实目录树，深度 2-3 层]
\`\`\`

### 模块说明

#### [层次/模块名]
- **职责**: [从代码读取的真实职责]
- **规范**: [从代码中归纳出的规范，如注解使用、返回类型]

[继续描述其他层次]
```

---

## Step 5 输出模板：外部依赖

```markdown
## 外部依赖

### 核心框架依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| [框架名] | [版本] | [用途] |

### 数据存储

| 技术 | 版本 | 用途 |
|------|------|------|
| [数据库] | [版本] | [用途，来源: 配置文件] |

### 第三方服务

#### [服务名]
- **用途**: [用途]
- **配置**: [配置文件位置和 key 前缀]
- **使用位置**: [调用代码文件]

### 工具库

| 依赖 | 版本 | 用途 |
|------|------|------|

### 开发和测试

| 依赖 | 版本 | 用途 |
|------|------|------|
```

---

## Step 6 输出模板：两层文档骨架

文档拆分到 `docs/project-overview/`（全局层）和 `docs/domains/<X>/`（领域层）。下面按文件给出模板。

### DOMAIN_MAP 格式

写入 `project-overview/README.md` 头部，紧跟 DOC_META 之后。YAML 内容用 HTML 注释包裹，对渲染不可见但可被 skill 解析。

```markdown
<!-- DOC_META: last_commit=abc123def456, generated=2026-04-21 -->

<!-- DOMAIN_MAP
order:
  paths:
    - src/main/java/com/xxx/order/**
    - src/main/java/com/xxx/trade/**
  entities: [Order, OrderItem, OrderAddress]
  responsibility: 订单创建、状态流转、订单查询
payment:
  paths:
    - src/main/java/com/xxx/payment/**
  entities: [Payment, Refund]
  responsibility: 支付受理、退款、对账
user:
  paths:
    - src/main/java/com/xxx/user/**
  entities: [User, UserProfile, LoginLog]
  responsibility: 账户管理、注册、认证
-->
```

**字段约定**：
- `paths`：glob 模式列表，增量更新按此分桶；每个源文件应命中唯一一个域
- `entities`：**归属本域**的核心实体（不是"本域用到的实体"）
- `responsibility`：一句话职责（可选，用于 `domains/README.md` 清单）

**设计原则**：每个实体归属唯一一个域；User 虽然被 order、payment 引用，仍只在 user 域列出一次。跨域引用通过文档里的相对链接表达，不在 DOMAIN_MAP 体现。

---

### 全局层

#### `docs/project-overview/README.md`（入口）

```markdown
<!-- DOC_META: last_commit=<HEAD commit 12 位，非 git 填 none>, generated=<当前日期 YYYY-MM-DD> -->

<!-- DOMAIN_MAP
<Step 1.5 确认的 YAML 映射>
-->

# [项目名称] - 项目概览

> 生成时间: [当前日期]
> 代码版本: [Git commit 短 hash 12 位，非 git 填 none]

## 项目简介

- **项目类型**: [Web 应用 / 微服务 / 库 / CLI 工具等]
- **技术栈**: [主要技术栈]（来源: [构建文件]）
- **版本**: [当前版本]（来源: [构建文件]）
- **构建工具**: [Maven / Gradle / npm / pnpm / cargo 等]

### 项目目标
[从 README 或代码推断的项目目标和用途。若纯推断，标注 [推断]]

## 业务域

| 域 | 职责 | 核心实体 | 文档 |
|----|------|---------|------|
| order | 订单创建、状态流转 | Order, OrderItem | [../domains/order/](../domains/order/README.md) |
| payment | 支付受理、退款 | Payment, Refund | [../domains/payment/](../domains/payment/README.md) |
| user | 账户管理、认证 | User, UserProfile | [../domains/user/](../domains/user/README.md) |

完整清单：[领域索引](../domains/README.md)

## 文档目录

**项目层**（本目录）：
- [项目结构](./architecture.md) — 架构模式、目录组织、领域划分、跨域 ER 主图
- [外部依赖](./dependencies.md) — 框架、库、第三方服务
- [部署说明](./deployment.md) — 环境要求、启动步骤
- [开发指南](./development.md) — 本地开发、代码规范

**领域层**：
- [领域清单](../domains/README.md) — 所有业务域索引，各域的实体 / 流程 / API 在各自目录

## 文档维护

本文档由 AI 自动生成，基于代码库快照。

**更新文档**: 代码有重大变更时重新调用 skill（默认增量；说"重新生成"触发全量）。

**手动维护**（AI 无法推断的部分）:
- 业务背景和决策原因
- 架构演进历史
- 性能指标与优化建议
```

---

### `docs/project-overview/architecture.md`

```markdown
# 项目结构

[返回概览](./README.md)

## 架构模式
本项目采用 **[分层架构 / 六边形 / 微服务 / 模块化单体]** 模式。
**判断依据**: [目录结构 / 包命名 / 关键注解]

## 目录结构
\`\`\`
[使用 Glob 扫描得到的真实目录树，按语言自适应深度]
\`\`\`

## 领域划分

<!-- 根据 project-overview/README.md 头部的 DOMAIN_MAP 渲染 -->

| 域 | paths | 核心实体（归属本域）| 职责 |
|----|-------|---------------------|------|
| order | `src/main/java/com/xxx/order/**` | Order, OrderItem | 订单创建、状态流转 |
| payment | `src/main/java/com/xxx/payment/**` | Payment, Refund | 支付受理、退款 |
| user | `src/main/java/com/xxx/user/**` | User, UserProfile | 账户管理、认证 |

### 跨域 ER 主图

> 只展示**跨域引用**的实体关系，域内细节请看各域的 `domain-model.md`。

\`\`\`mermaid
erDiagram
    User ||--o{ Order : "placed by (referenced by order)"
    User ||--o{ Payment : "paid by (referenced by payment)"
\`\`\`

## 模块说明

### [层次/模块名]
- **职责**: [从代码读取的真实职责]
- **规范**（从代码归纳）: [注解使用、返回类型等]

[继续描述其他层次]
```

---

### `docs/project-overview/dependencies.md`

```markdown
# 外部依赖

[返回概览](./README.md)

## 核心框架依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| [框架名] | [版本] | [用途] |

## 数据存储

| 技术 | 版本 | 用途 |
|------|------|------|
| [数据库] | [版本] | [用途]（来源: 配置文件） |

## 第三方服务

### [服务名]
- **用途**: [用途]
- **配置**: [配置文件位置和 key 前缀]
- **使用位置**: [调用代码文件]

## 工具库

| 依赖 | 版本 | 用途 |
|------|------|------|

## 开发和测试

| 依赖 | 版本 | 用途 |
|------|------|------|
```

---

### `docs/project-overview/deployment.md`

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

### `docs/project-overview/development.md`

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

### 领域层

#### `docs/domains/README.md`（领域清单）

```markdown
# 业务域清单

[返回项目总览](../project-overview/README.md)

> 每个域自包含：实体、流程、API 都在各自目录。跨域实体引用通过链接指向归属域（如 Order 引用 User 时链接到 user 域）。

| 域 | 职责 | 核心实体 | 入口 | 文档 |
|----|------|---------|------|------|
| order | 订单创建、状态流转 | Order, OrderItem | `OrderController` | [./order/](./order/README.md) |
| payment | 支付受理、退款 | Payment, Refund | `PaymentController` | [./payment/](./payment/README.md) |
```

#### `docs/domains/<X>/README.md`（单文件模式）

小域默认模板（实体 < 4 个、流程 < 3 个、总量预估 < 400 行）。

```markdown
# Order 领域

[返回项目总览](../../project-overview/README.md) · [返回领域清单](../README.md)

## 领域职责
订单的创建、状态流转、查询与取消。

## 对外接口

**REST API**（来源: `OrderController.java`）:
- `POST /api/orders` — 创建订单
- `GET /api/orders/{id}` — 查询订单
- `POST /api/orders/{id}/cancel` — 取消订单

**事件**（来源: `OrderEventPublisher.java`）:
- 发布：`OrderCreated`、`OrderCancelled`
- 订阅：`PaymentCompleted`（来自 payment 域）

## 核心实体

### Order (订单)
- **来源文件**: `order/entity/Order.java`
- **关键字段**:
  - `id`: 订单 ID
  - `userId`: 下单用户（引用 [User](../user/domain-model.md#user)，归属 user 域）
  - `status`: 订单状态（见下方状态机）
  - `totalAmount`: 订单总额
- **业务规则**（仅列出代码可验证）:
  - 创建后 30 分钟未支付自动取消（来源: `OrderScheduler.java:23`）
- **被其他域引用**: audit 域（操作日志记录）

### OrderItem (订单项)
[...]

## 主要流程

### 创建订单流程（单域）
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

### 下单支付流程（跨域，归属本域）
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

[对本域每个主要流程重复，上限 5 个]

## 状态机（如有）

### Order 状态机
**来源**: `order/entity/OrderStatus.java` + `OrderService.transitionTo`

\`\`\`mermaid
stateDiagram-v2
    [*] --> PENDING: 创建
    PENDING --> PAID: 支付成功
    PENDING --> CANCELLED: 超时/取消
\`\`\`

## 实现位置
- Controller: `order/controller/`
- Service: `order/service/`
- Repository: `order/repository/`
- Entity: `order/entity/`

## 其他端点

| 方法 | 端点 | 入口 | 简述 |
|------|------|------|------|
| GET | `/api/orders` | `OrderController.list` | 订单列表分页 |

## 被跨域流程调用

> 当本域的 Service 被其他域的流程调用时填写。无则省略本节。

| 本域接口 | 调用方域 | 跨域流程 |
|---------|---------|---------|
| `OrderService.updateStatus` | payment | [退款到账](../payment/flows.md#退款到账) |
```

#### `docs/domains/<X>/` 拆分模式

大域触发拆分（任一条件：实体 ≥ 4、流程 ≥ 3、预估 > 400 行）时，拆成 3 个文件。

**`<X>/README.md`**（拆分模式的概览）

```markdown
# Order 领域

[返回项目总览](../../project-overview/README.md) · [返回领域清单](../README.md)

## 领域职责
订单的创建、状态流转、查询与取消。

## 对外接口

**REST API**（来源: `OrderController.java`）:
- `POST /api/orders` — 创建订单
- [完整列表略，见本域 Controller]

**事件**（来源: `OrderEventPublisher.java`）:
- 发布：`OrderCreated`、`OrderCancelled`

## 实现位置
- Controller: `order/controller/`
- Service: `order/service/`
- Repository: `order/repository/`
- Entity: `order/entity/`

## 章节

- [领域模型](./domain-model.md) — 本域实体、关系、业务规则
- [业务流程](./flows.md) — 本域流程、状态机、端点清单
```

**`<X>/domain-model.md`**

```markdown
# Order 领域模型

[返回 Order 领域](./README.md) · [领域清单](../README.md) · [项目总览](../../project-overview/README.md)

## 实体关系图（本域）

\`\`\`mermaid
erDiagram
    Order ||--|{ OrderItem : contains
    Order }o--|| User : "placed by (ref user 域)"
\`\`\`

> 跨域引用（如 User）只画关系线，实体详情见归属域。

## 核心实体

### Order (订单)
[同单文件模式的实体格式；跨域字段用 `引用 [EntityName](../<other-domain>/domain-model.md#xxx)`]

## 次要实体

| 实体 | 用途 | 来源文件 |
|------|------|---------|
| ... | ... | ... |
```

**`<X>/flows.md`**

```markdown
# Order 业务流程

[返回 Order 领域](./README.md) · [领域清单](../README.md) · [项目总览](../../project-overview/README.md)

## 主要流程

### 创建订单流程
[同单文件模式的流程格式；跨域流程按归属规则放在归属域]

## 状态机

### Order 状态机
[状态机图]

## 其他端点

| 方法 | 端点 | 入口 | 简述 |
|------|------|------|------|

## 被跨域流程调用

> 当本域的 Service 被其他域的流程调用时填写。无则省略本节。

| 本域接口 | 调用方域 | 跨域流程 |
|---------|---------|---------|
| `OrderService.updateStatus` | payment | [退款到账](../payment/flows.md#退款到账) |
```
```
