---
name: document-project
description: Analyze existing codebase and generate comprehensive project documentation including overview, domain models, business flows, architecture, and dependencies. Use when the user asks to document a project, create project documentation, analyze codebase structure, or mentions terms like "项目文档", "整理文档", "项目说明".
---

# Project Documentation Generator

从现有代码库自动生成全面的项目文档，包括项目简介、核心领域模型、业务流程、项目结构和外部依赖分析。

## Quick Start

当用户请求生成项目文档时，**首先执行 Step 0 判断模式**，再按对应流程执行。

## Step 0: 前置检查（必须首先执行）

检查目标文件 `docs/PROJECT_DOCUMENTATION.md` 是否已存在：

```bash
# 检查文件是否存在
ls docs/PROJECT_DOCUMENTATION.md
```

### 文件已存在 → 增量更新模式

如果文档已存在，**不要走完整的 Step 1-6 流程**，改为：

1. **读取原文档**：完整读取现有文档内容，了解已有结构和信息
2. **分析代码变更**：通过 `git log` 和 `git diff` 找出自上次文档生成以来的代码变更
   ```bash
   # 从原文档中提取上次的 commit hash
   # 对比变更
   git diff <old_commit> HEAD --stat
   git diff <old_commit> HEAD
   ```
3. **增量更新**：仅针对变更部分更新文档（新增章节、修改描述、更新版本号等），保留原文档中未变更的内容
4. **更新元信息**：更新文档头部的生成时间、commit hash 和版本号

### 文件不存在 → 全量生成模式

按以下完整流程执行：

```
Task Progress:
- [ ] Step 1: 项目概览分析
- [ ] Step 2: 领域模型提取
- [ ] Step 3: 业务流程梳理
- [ ] Step 4: 架构结构分析
- [ ] Step 5: 依赖关系整理
- [ ] Step 6: 生成完整文档
```

## Step 1: 项目概览分析

### 1.1 识别项目类型

检查以下文件确定项目类型：
- `pom.xml` / `build.gradle` → Java/Spring 项目
- `package.json` → Node.js/前端项目
- `requirements.txt` / `pyproject.toml` → Python 项目
- `go.mod` → Go 项目
- `Cargo.toml` → Rust 项目

### 1.2 收集基础信息

从配置文件中提取：
- 项目名称和版本
- 技术栈（框架、语言版本）
- 构建工具和打包方式
- 主要配置文件位置

### 1.3 分析 README 和现有文档

检查是否存在：
- `README.md` / `README.txt`
- `docs/` 目录
- `CHANGELOG.md`
- API 文档

**输出格式：**
```markdown
# [项目名称]

## 项目简介
- **项目类型**: [Web应用/微服务/库/工具等]
- **技术栈**: [主要技术栈]
- **版本**: [当前版本]
- **构建工具**: [Maven/Gradle/npm等]

## 项目目标
[从 README 或代码推断的项目目标和用途]
```

## Step 2: 领域模型提取

### 2.1 定位实体类

根据项目类型查找：
- **Java**: `**/entity/**`, `**/model/**`, `**/domain/**`, `@Entity` 注解
- **Python**: `**/models.py`, `**/entities.py`, dataclass/pydantic 模型
- **Node.js**: `**/models/**`, `**/entities/**`, TypeScript interfaces
- **Go**: `**/model/**`, struct 定义

### 2.2 分析实体关系

识别：
- 主键和外键关系
- 一对多、多对多关系（`@OneToMany`, `@ManyToMany` 等）
- 继承关系
- 组合关系

### 2.3 提取核心业务概念

对每个核心实体记录：
- 实体名称和用途
- 关键字段及其含义
- 业务规则和约束
- 与其他实体的关系

**输出格式：**
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
- **关键字段**:
  - `id`: 用户唯一标识
  - `username`: 用户名
  - `email`: 邮箱地址
  - `role`: 用户角色（ADMIN/USER）
- **业务规则**:
  - 用户名必须唯一
  - 邮箱需要验证
- **关联关系**:
  - 一个用户可以有多个订单

[对每个核心实体重复此格式]
```

## Step 3: 业务流程梳理

### 3.1 识别业务入口

查找：
- **REST API**: `@RestController`, `@RequestMapping`, Express routes
- **GraphQL**: Resolvers, schema 定义
- **消息队列**: `@RabbitListener`, `@KafkaListener`
- **定时任务**: `@Scheduled`, cron jobs
- **事件处理**: Event handlers, webhooks

### 3.2 追踪业务流程

对每个主要业务场景：
1. 从入口点开始（Controller/Handler）
2. 追踪 Service 层调用
3. 识别数据访问层（Repository/DAO）
4. 记录外部调用（第三方 API、消息队列）
5. 标注事务边界和异常处理

### 3.3 绘制流程图

使用 Mermaid 语法：

**输出格式：**
```markdown
## 业务流程

### 用户注册流程
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

**关键步骤说明**:
1. **邮箱唯一性检查**: 防止重复注册
2. **密码加密**: 使用 BCrypt 加密存储
3. **发送验证邮件**: 异步发送，不阻塞主流程
4. **事务管理**: 整个注册过程在一个事务中

**异常处理**:
- `EmailAlreadyExistsException`: 邮箱已被注册
- `EmailSendFailureException`: 邮件发送失败（记录日志但不回滚）

[对每个主要业务流程重复此格式]
```

## Step 4: 架构结构分析

### 4.1 分析目录结构

执行：
```bash
tree -L 3 -I 'node_modules|target|build|dist' > structure.txt
```

或使用 Glob 工具查找主要目录。

### 4.2 识别架构模式

判断项目采用的架构：
- **分层架构**: Controller → Service → Repository
- **六边形架构**: Domain → Application → Infrastructure
- **微服务架构**: 多个独立服务
- **模块化单体**: 按业务域划分模块

### 4.3 分析代码组织

识别：
- 包/模块的职责划分
- 公共组件和工具类
- 配置管理方式
- 测试代码组织

**输出格式：**
```markdown
## 项目结构

### 架构模式
本项目采用 **分层架构** + **领域驱动设计（DDD）** 模式。

### 目录结构
\`\`\`
src/main/java/com/example/project/
├── controller/          # 控制器层 - 处理 HTTP 请求
│   ├── AuthController.java
│   └── UserController.java
├── service/             # 服务层 - 业务逻辑
│   ├── UserService.java
│   └── impl/
│       └── UserServiceImpl.java
├── repository/          # 数据访问层
│   └── UserRepository.java
├── entity/              # 实体类 - 领域模型
│   └── User.java
├── dto/                 # 数据传输对象
│   ├── request/
│   └── response/
├── config/              # 配置类
│   ├── SecurityConfig.java
│   └── DatabaseConfig.java
├── exception/           # 异常定义
│   └── GlobalExceptionHandler.java
└── util/                # 工具类
    └── DateUtil.java

src/main/resources/
├── application.yml      # 主配置文件
├── application-dev.yml  # 开发环境配置
└── application-prod.yml # 生产环境配置
\`\`\`

### 模块说明

#### Controller 层
- **职责**: 接收 HTTP 请求，参数验证，调用 Service，返回响应
- **规范**:
  - 使用 `@RestController` 注解
  - 统一返回 `Result<T>` 包装类
  - 使用 `@Valid` 进行参数校验

#### Service 层
- **职责**: 核心业务逻辑，事务管理，调用多个 Repository
- **规范**:
  - 接口与实现分离
  - 使用 `@Transactional` 管理事务
  - 避免直接操作 Entity，使用 DTO 传递数据

#### Repository 层
- **职责**: 数据持久化，数据库操作
- **规范**:
  - 继承 `JpaRepository` 或 `MyBatis Mapper`
  - 只包含数据访问逻辑，不包含业务逻辑

[继续描述其他层次]
```

## Step 5: 依赖关系整理

### 5.1 分析外部依赖

从构建文件中提取：
- **Java**: `pom.xml` 或 `build.gradle`
- **Node.js**: `package.json`
- **Python**: `requirements.txt` 或 `pyproject.toml`

### 5.2 分类依赖

按用途分类：
- **核心框架**: Spring Boot, Express, Django 等
- **数据库**: MySQL, PostgreSQL, MongoDB 驱动
- **缓存**: Redis, Memcached
- **消息队列**: RabbitMQ, Kafka
- **工具库**: Lombok, Guava, Lodash
- **测试**: JUnit, Mockito, Jest

### 5.3 识别外部服务

从配置文件和代码中查找：
- 第三方 API 调用
- 云服务集成（AWS, 阿里云等）
- 支付网关
- 短信/邮件服务

**输出格式：**
```markdown
## 外部依赖

### 核心框架依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Spring Boot | 2.7.5 | 应用框架 |
| Spring Security | 2.7.5 | 安全认证 |
| Spring Data JPA | 2.7.5 | 数据访问 |

### 数据存储

| 技术 | 版本 | 用途 |
|------|------|------|
| MySQL | 8.0 | 主数据库 |
| Redis | 6.2 | 缓存、会话存储 |
| Elasticsearch | 7.17 | 全文搜索 |

### 第三方服务

#### 阿里云 OSS
- **用途**: 文件存储
- **配置**: `application.yml` 中的 `aliyun.oss.*`
- **使用位置**: `FileService.java`

#### 微信支付
- **用途**: 支付处理
- **配置**: `application.yml` 中的 `wechat.pay.*`
- **使用位置**: `PaymentService.java`

### 工具库

| 依赖 | 版本 | 用途 |
|------|------|------|
| Lombok | 1.18.24 | 简化 Java 代码 |
| Hutool | 5.8.10 | Java 工具类库 |
| Jackson | 2.13.4 | JSON 序列化 |

### 开发和测试

| 依赖 | 版本 | 用途 |
|------|------|------|
| JUnit 5 | 5.9.1 | 单元测试 |
| Mockito | 4.8.0 | Mock 框架 |
| SpringDoc OpenAPI | 1.6.12 | API 文档生成 |
```

## Step 6: 生成完整文档

### 6.1 组装文档

将以上所有部分组合成一个完整的文档，按以下结构：

```markdown
# [项目名称] - 项目文档

> 生成时间: [当前日期]
> 代码版本: [Git commit hash]

## 目录
- [项目简介](#项目简介)
- [核心领域模型](#核心领域模型)
- [业务流程](#业务流程)
- [项目结构](#项目结构)
- [外部依赖](#外部依赖)
- [部署说明](#部署说明)
- [开发指南](#开发指南)

[插入前面步骤生成的所有内容]

## 部署说明

### 环境要求
- Java 11+
- MySQL 8.0+
- Redis 6.2+

### 配置说明
1. 复制 `application-example.yml` 为 `application-prod.yml`
2. 修改数据库连接信息
3. 配置 Redis 连接
4. 设置第三方服务密钥

### 启动步骤
\`\`\`bash
# 构建
./gradlew build

# 运行
java -jar build/libs/app.jar --spring.profiles.active=prod
\`\`\`

## 开发指南

### 本地开发环境搭建
[步骤说明]

### 代码规范
[编码规范说明]

### 提交规范
[Git commit 规范]

### 常见问题
[FAQ]
```

### 6.2 保存文档

将生成的文档保存到：
- `docs/PROJECT_DOCUMENTATION.md` (推荐)
- 或项目根目录的 `DOCUMENTATION.md`

### 6.3 生成摘要

为用户提供简短的文档摘要，突出：
- 项目的核心功能
- 主要技术栈
- 关键业务流程数量
- 核心实体数量
- 文档保存位置

## 分析技巧

### 代码推断技巧

当信息不完整时，从代码推断：
- **项目用途**: 从 Controller 的端点名称推断
- **业务规则**: 从 Service 层的验证逻辑推断
- **数据关系**: 从 JPA 注解或 SQL 查询推断
- **集成服务**: 从配置文件的 key 名称推断

### 使用工具高效分析

1. **SemanticSearch**: 查找特定模式
   ```
   "Where are the main entity classes defined?"
   "How is authentication implemented?"
   ```

2. **Grep**: 精确搜索
   ```
   @Entity
   @RestController
   @Transactional
   ```

3. **Glob**: 查找特定文件
   ```
   **/*Controller.java
   **/*Service.java
   **/entity/*.java
   ```

### 处理大型项目

对于超过 100 个文件的项目：
1. **优先分析核心模块**: 先处理 `core/`, `domain/`, `service/` 等核心目录
2. **采样分析**: 每个模块选择 2-3 个代表性文件深入分析
3. **渐进式文档**: 先生成框架，再逐步填充细节
4. **使用 Task 工具**: 并行分析不同模块

```
Task 1: 分析用户模块
Task 2: 分析订单模块
Task 3: 分析支付模块
```

## 输出质量检查

生成文档后，验证：
- [ ] 所有章节都有实质内容（不是占位符）
- [ ] Mermaid 图表语法正确
- [ ] 代码引用使用正确的行号格式
- [ ] 表格格式正确对齐
- [ ] 专业术语使用一致
- [ ] 中英文混排时有适当空格

## 常见项目类型模板

### Spring Boot 项目
重点关注：
- `@SpringBootApplication` 主类
- `application.yml` 配置
- JPA Entity 和 Repository
- REST Controller
- Security 配置

### Node.js/Express 项目
重点关注：
- `package.json` 依赖
- `app.js` 或 `index.js` 入口
- Routes 定义
- Middleware
- Database models (Mongoose, Sequelize)

### Django 项目
重点关注：
- `settings.py` 配置
- `models.py` 模型定义
- `views.py` 视图
- `urls.py` 路由
- `admin.py` 管理界面

## 示例输出

完整示例请参考 [example-output.md](example-output.md)

## 最佳实践

1. **保持客观**: 基于代码事实，避免主观评价
2. **使用图表**: 复杂关系用 Mermaid 图表展示
3. **提供上下文**: 不仅说"是什么"，还要说"为什么"
4. **标注来源**: 重要信息标注来源文件
5. **持续更新**: 建议在 README 中添加"文档生成命令"

## 文档维护建议

在生成的文档末尾添加：

```markdown
## 文档维护

本文档由 AI 自动生成，基于代码库快照。

**更新文档**:
当代码有重大变更时，调用相关命令让 AI 重新生成文档

**手动维护**:
- 业务背景和决策原因需要手动补充
- 架构演进历史需要手动记录
- 性能优化建议需要手动添加
```
