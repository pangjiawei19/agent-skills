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

## Step 6 输出模板：多文件拆分骨架

文档固定拆分到 `docs/project-overview/` 目录下 7 个文件。以下是每个文件的模板。

---

### `docs/project-overview/README.md`（入口）

```markdown
<!-- DOC_META: last_commit=<HEAD commit 12 位，非 git 填 none>, generated=<当前日期 YYYY-MM-DD> -->

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

## 文档目录

- [核心领域模型](./domain-model.md) — 实体、ER 图、业务规则
- [业务流程](./business-flows.md) — 主要流程序列图、状态机
- [项目结构](./architecture.md) — 架构模式、目录组织
- [外部依赖](./dependencies.md) — 框架、库、第三方服务
- [部署说明](./deployment.md) — 环境要求、启动步骤
- [开发指南](./development.md) — 本地开发、代码规范

## 文档维护

本文档由 AI 自动生成，基于代码库快照。

**更新文档**: 当代码有重大变更时，重新调用 document-project skill（默认增量更新，说"重新生成"触发全量）。

**手动维护**（AI 无法推断的部分）:
- 业务背景和决策原因
- 架构演进历史
- 性能指标与优化建议
```

---

### `docs/project-overview/domain-model.md`

```markdown
# 核心领域模型

[返回概览](./README.md)

## 实体关系图

\`\`\`mermaid
erDiagram
    User ||--o{ Order : places
    Order ||--|{ OrderItem : contains
    Product ||--o{ OrderItem : "ordered in"
\`\`\`

## 核心实体

### User (用户)
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

[对每个核心实体重复，上限 10-15 个]

## 次要实体

| 实体 | 用途 | 来源文件 |
|------|------|---------|
| `LoginLog` | 登录日志 | `entity/LoginLog.java` |
| `AuditLog` | 审计日志 | `entity/AuditLog.java` |
```

---

### `docs/project-overview/business-flows.md`

```markdown
# 业务流程

[返回概览](./README.md)

## 主要流程

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

[对每个主要流程重复，上限 5-8 个]

## 状态机

### 订单状态机
**来源**: `entity/OrderStatus.java` + `OrderService.transitionTo():xxx`

\`\`\`mermaid
stateDiagram-v2
    [*] --> PENDING: 创建
    PENDING --> PAID: 支付成功
    PENDING --> CANCELLED: 超时/取消
\`\`\`

## 其他端点

| 方法 | 端点 | 入口 | 简述 |
|------|------|------|------|
| GET | `/api/users/{id}` | `UserController.getUser` | 查询用户详情 |
| GET | `/api/orders` | `OrderController.list` | 订单列表分页 |
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
