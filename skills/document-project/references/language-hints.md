# 按语言 / 框架的定位提示

当识别出项目类型后，加载本文件查阅对应的"在哪里找实体 / 入口 / 依赖 / 配置"提示。

---

## Java / Spring Boot

### 项目信号
- `pom.xml` 含 `spring-boot-starter-parent`
- `build.gradle` 含 `org.springframework.boot` 插件
- 主类带 `@SpringBootApplication`

### 领域识别（Step 1.5 用）

**首选信号**：package 路径 `com.<company>.<project>.<domain>.*`，其中 `<domain>` 段通常就是业务域名。

```bash
# 扫描所有业务 package（过滤基础层）
# 常见"非业务 package"：config, common, util, infrastructure, gateway
```

**推断步骤**：
1. 找到主包（`@SpringBootApplication` 所在包的父包，如 `com.xxx.shop`）
2. 列出主包下的所有子 package（深度 1）
3. 过滤掉 `config` / `common` / `util` / `infrastructure` / `gateway` / `shared` 等基础 package
4. 剩下的每个子 package 推断为一个业务域

**次要信号**（主信号不明显时）：
- 扁平项目：按 `*Controller` / `*Service` 前缀聚类（`OrderController` + `OrderService` + `OrderRepository` → `order`）
- DDD 项目：`domain/` 或 `aggregate/` 子目录每个子项是一个聚合 = 一个域

**典型 paths 写法**：
```yaml
order:
  paths:
    - src/main/java/com/xxx/shop/order/**
    - src/test/java/com/xxx/shop/order/**
```

### 实体定位
- 目录：`**/entity/**`、`**/model/**`、`**/domain/**`
- 注解：`@Entity`、`@Table`、`@Document`（MongoDB）
- 关系注解：`@OneToMany`、`@ManyToOne`、`@ManyToMany`、`@JoinColumn`

### 业务入口
- REST: `@RestController`、`@RequestMapping`、`@GetMapping` 等
- GraphQL: `@QueryMapping`、`@SchemaMapping`
- MQ: `@RabbitListener`、`@KafkaListener`、`@StreamListener`
- 定时: `@Scheduled`
- 事件: `@EventListener`

### 依赖来源
- `pom.xml` `<dependencies>` / `build.gradle` `dependencies {}`
- 配置：`application.yml` / `application-*.yml` / `application.properties`

### 重点关注
- `@SpringBootApplication` 主类位置
- `SecurityConfig` / `WebSecurityConfigurerAdapter`
- `@Transactional` 边界
- `@ConfigurationProperties` 绑定

---

## Node.js / Express / NestJS

### 项目信号
- `package.json` 含 `express` / `@nestjs/core` / `koa` / `fastify`
- 入口：`index.js` / `app.js` / `server.js` / `src/main.ts`（NestJS）

### 领域识别（Step 1.5 用）

**首选信号**：顶层功能目录。
- NestJS：`src/<module>/` 每个子目录通常一个 Module，对应一个业务域（`src/order/`、`src/payment/`）
- Express：`src/modules/<domain>/` 或 `src/features/<domain>/` 结构
- 扁平 Express：按 `routes/<domain>.js` + `services/<domain>.js` 文件名聚类

**过滤非业务目录**：`common` / `shared` / `utils` / `config` / `middlewares` / `infrastructure`。

**NestJS Module 识别**：每个 `*.module.ts` 文件所在目录 = 一个域（除非是 `AppModule` 或明显的基础模块）。

**典型 paths**：
```yaml
order:
  paths:
    - src/order/**
    - src/orders/**  # 单复数都要考虑
```

### 实体 / 模型定位
- **Mongoose**: `**/models/**`、`mongoose.Schema` / `@Schema()`（NestJS + Mongoose）
- **Sequelize / TypeORM**: `**/entities/**`、`@Entity()`、`@Column()`
- **Prisma**: `prisma/schema.prisma`
- **纯 TS**: `**/interfaces/**`、`**/types/**`、`**/dto/**`

### 业务入口
- Express: `app.get/post/...` 路由定义、`router.use()`
- NestJS: `@Controller()` + `@Get()/@Post()` 等、`@MessagePattern()`
- 中间件：`app.use(...)` / `@UseGuards()` / `@UseInterceptors()`

### 依赖来源
- `package.json` `dependencies` / `devDependencies`
- `pnpm-workspace.yaml` / `turbo.json` / `nx.json`（monorepo）
- 配置：`.env.example`、`config/*.js`、`@nestjs/config` 模块

### 重点关注
- `package.json` 的 `scripts` 字段（启动命令）
- `tsconfig.json` 的 paths 和 target
- 中间件链 / NestJS 的 Module 结构

---

## Python / Django / Flask / FastAPI

### 项目信号
- `pyproject.toml` / `requirements.txt` / `setup.py`
- `manage.py`（Django）、`app.py` / `main.py`（Flask/FastAPI）

### 领域识别（Step 1.5 用）

**Django**：每个 app（`manage.py startapp` 创建）通常就是一个业务域。扫描 `INSTALLED_APPS` 里的本地 app（过滤 `django.contrib.*` 等第三方）。

**FastAPI / Flask**：
- 首选 `app/<domain>/` 或 `src/<domain>/` 顶层子目录
- `routers/<domain>.py` + `models/<domain>.py` + `services/<domain>.py` 命名聚类

**过滤非业务目录**：`core` / `common` / `utils` / `config` / `middleware` / `deps`。

**典型 paths**：
```yaml
order:
  paths:
    - app/order/**
    - app/orders/**
# Django
order:
  paths:
    - order/**  # Django app 在项目根
```

### 实体 / 模型定位
- **Django**: `**/models.py`、`models.Model`
- **SQLAlchemy**: `**/models/**`、`Base = declarative_base()`
- **Pydantic / FastAPI**: `BaseModel` 子类、`**/schemas/**`
- **dataclass**: `@dataclass` 装饰器

### 业务入口
- Django: `urls.py` 路由 + `views.py` 视图 + `admin.py`
- Flask: `@app.route()` / `Blueprint`
- FastAPI: `@app.get()/@app.post()` 等、`APIRouter`
- Celery: `@shared_task` / `@app.task`

### 依赖来源
- `pyproject.toml` `[project.dependencies]`、`requirements*.txt`、`Pipfile`
- 配置：Django `settings.py`、FastAPI `.env` + `pydantic-settings`

### 重点关注
- Django: `INSTALLED_APPS`、`MIDDLEWARE`、迁移文件 `*/migrations/`
- FastAPI: dependency injection 树
- 虚拟环境管理（poetry / pipenv / uv）

---

## Go

### 项目信号
- `go.mod` 存在
- 入口：`main.go` 或 `cmd/*/main.go`

### 领域识别（Step 1.5 用）

**首选信号**：
- `internal/<domain>/` 子包（Go 项目惯例，每个子包一个域）
- `pkg/<domain>/`（对外导出的域）
- DDD 项目：`internal/domain/<aggregate>/`
- 微服务：`cmd/<service-name>/` 每个入口一个域（跨服务时每个服务单独处理）

**过滤非业务目录**：`config` / `common` / `utils` / `infra` / `middleware` / `pkg/errors` 等。

**典型 paths**：
```yaml
order:
  paths:
    - internal/order/**
    - internal/domain/order/**
```

### 实体 / 模型定位
- `**/model/**`、`**/entity/**`、`**/domain/**`
- `struct` 定义 + GORM 标签 `gorm:"..."`
- `sqlc` 生成的 `**/db/**`

### 业务入口
- Gin: `r.GET/POST(...)`、Handler 函数
- Echo: `e.GET/POST(...)`
- chi / gorilla mux: 同理
- gRPC: `*.proto` + 生成的 `*_grpc.pb.go`

### 依赖来源
- `go.mod` `require` 块
- 配置：`config/*.yaml`、`.env`、Viper

### 重点关注
- `cmd/` 多入口（微服务常见）
- `internal/` 私有包组织
- `pkg/` 对外公共包
- `Dockerfile` / `Makefile` 中的构建命令

---

## Rust

### 项目信号
- `Cargo.toml` 存在
- 入口：`src/main.rs`（binary）或 `src/lib.rs`（library）

### 领域识别（Step 1.5 用）

**首选信号**：
- 模块目录 `src/<domain>/mod.rs` 或 `src/<domain>.rs`
- Workspace 多 crate：每个 `<workspace-member>` 可能是一个域
- DDD 项目：`src/domain/<aggregate>/`

**过滤非业务模块**：`error` / `util` / `common` / `config` / `prelude`。

### 实体 / 模型定位
- `**/models/**`、`**/entities/**`
- `struct` + `#[derive(...)]`（Serde、Diesel、SeaORM）

### 业务入口
- **actix-web**: `#[get("...")]` / `#[post("...")]`
- **axum**: `Router::new().route(...)`
- **rocket**: `#[get("/...")]` / `#[post("/...")]`

### 依赖来源
- `Cargo.toml` `[dependencies]` / `[dev-dependencies]`
- workspace: `[workspace.members]`

### 重点关注
- `Cargo.toml` 的 `[features]`
- `build.rs` 构建脚本
- workspace 多 crate 组织

---

## Monorepo / 多模块项目

如果顶层出现以下信号之一，按 monorepo 处理：
- `apps/`、`packages/`、`services/`、`modules/` 目录结构
- `pnpm-workspace.yaml`、`turbo.json`、`nx.json`、`lerna.json`
- `go.work`、Gradle `settings.gradle` 含多 `include`
- Maven 父 `pom.xml` 含 `<modules>`

### 领域识别（Step 1.5 用）

Monorepo 天然按 service/package 分域：**每个顶层子项目 ≈ 一个域**。

```yaml
order-service:
  paths:
    - services/order-service/**
payment-service:
  paths:
    - services/payment-service/**
shared-libs:
  paths:
    - packages/common/**
    - packages/types/**
  # shared-libs 是基础设施性质，不作为业务域；放到 shared 或单独列出不进 domains/
```

**例外**：如果单个子项目内部业务复杂（如一个大 monolith service），仍需在该子项目内部继续按 package 做领域划分。

### 处理策略
1. 先在 Step 1 列出所有子模块及其角色
2. Step 2-5 分别针对每个**核心**子模块执行（非核心可合并描述）
3. 优先使用**并行派发子 agent**（见 SKILL.md "处理大型项目"），每个 agent 负责一个模块
4. 最终文档按 `模块 A / 模块 B / ...` 组织，或按"领域模型 / 业务流程"横向组织，选择更清晰的方式

---

## 通用排查清单

拿到项目后优先扫描这些文件（用于快速建立项目画像）：

| 文件 | 用途 |
|------|------|
| `README.md` / `README.*` | 项目目标、启动步骤 |
| `CONTRIBUTING.md` | 开发规范 |
| `CHANGELOG.md` | 版本演进 |
| `Dockerfile` / `docker-compose.yml` | 运行环境、启动命令 |
| `.github/workflows/*.yml` / `.gitlab-ci.yml` | CI 流程、测试命令 |
| `Makefile` / `justfile` / `Taskfile.yml` | 常用命令 |
| `.env.example` / `*.example.*` | 配置项清单 |
| `openapi.yaml` / `swagger.json` | API 契约 |
| `schema.prisma` / `*.sql` / `migrations/` | 数据模型 |
