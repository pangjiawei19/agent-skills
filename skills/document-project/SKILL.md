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

**加载策略**：Step 1 识别项目类型后加载 language-hints.md；需要输出格式时加载 output-templates.md。

## Quick Start

当用户请求生成项目文档时，**首先执行 Step 0 判断模式**，再按对应流程执行。

---

## Step 0: 前置检查（必须首先执行）

### 0.1 判断用户意图

用户显式要求"重新生成"、"rewrite"、"从头生成"、"全量更新"等 → 直接走**全量生成模式**，跳过下面的检查。

### 0.2 检查目标文件

使用 `Glob` 或等价能力检查 `docs/PROJECT_DOCUMENTATION.md` 是否存在。

### 0.3 提取上次生成的 commit 锚点

如果文件存在，读取文档头部的机器可读锚点：

```markdown
<!-- DOC_META: last_commit=abc123def, generated=2026-04-13 -->
```

- **找到锚点** → 进入 0.4 判断变更规模
- **未找到锚点**（旧文档未写入锚点） → 提示用户"未找到版本锚点，建议走全量重生成"，征得同意后走全量；若用户坚持增量，尝试用 `git log -1 --format=%H -- docs/PROJECT_DOCUMENTATION.md` 推断基准 commit，若该命令也返回空（文件未纳入版本控制），则**强制走全量**并明确告知用户

### 0.4 判断变更规模，决定模式

```bash
git diff <last_commit> HEAD --name-only | wc -l
git diff <last_commit> HEAD --stat
```

| 情况 | 模式 |
|------|------|
| 变更文件 < 10% 且无结构性变更 | **增量更新** |
| 变更文件 10%-30% | **增量更新**，重新扫描受影响章节 |
| 变更文件 > 30% | 提示用户"变更规模较大，建议全量重生成" |
| 出现结构性变更* | 提示用户"检测到结构性变更，建议全量重生成" |

**结构性变更**信号（任一命中即视为结构性）：
- 构建文件变动（`pom.xml` / `package.json` / `pyproject.toml` / `go.mod` / `Cargo.toml`）
- 顶层目录新增或删除（如新增 `apps/`、`services/`）
- 主类 / 入口文件变动
- 数据库迁移文件新增

### 增量更新流程

1. **读取原文档**，保留未变更章节
2. **聚焦变更文件**：只对 `git diff` 返回的文件执行 Step 1-5 中的相关分析
3. **更新受影响章节**：
   - 实体类变更 → 更新"核心领域模型"
   - Controller / Service 变更 → 更新"业务流程"
   - 构建文件变更 → 更新"外部依赖"
   - 目录变更 → 更新"项目结构"
4. **更新锚点和头部元信息**：
   ```markdown
   <!-- DOC_META: last_commit=<HEAD commit>, generated=<今天日期> -->
   ```

### 全量生成流程

```
Task Progress:
- [ ] Step 1: 项目概览分析
- [ ] Step 2: 领域模型提取
- [ ] Step 3: 业务流程梳理
- [ ] Step 4: 架构结构分析
- [ ] Step 5: 依赖关系整理
- [ ] Step 6: 生成完整文档
```

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

### 1.2 收集基础信息

从构建文件提取：项目名称、版本、技术栈、构建工具、主要配置文件位置。

### 1.3 扫描通用排查清单

优先读取：`README.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、`Dockerfile`、`docker-compose.yml`、CI 配置（`.github/workflows/*`、`.gitlab-ci.yml`）、`Makefile`、`.env.example`、`openapi.yaml`。

输出格式见 [references/output-templates.md#step-1](references/output-templates.md)。

---

## Step 2: 领域模型提取

### 2.1 定位实体类

按项目类型选择查找策略，详见 [references/language-hints.md](references/language-hints.md) 的"实体定位"小节。

### 2.2 分析实体关系

识别主键/外键、一对多/多对多、继承、组合关系。优先使用框架注解（`@OneToMany`、`gorm` 标签、Prisma schema 等）作为事实来源。

### 2.3 提取核心业务概念

对每个核心实体记录：
- **实体名称和用途**（来源文件）
- **关键字段及含义**
- **业务规则**（⚠️ 只列出代码中可验证的规则，不要凭经验脑补）
- **关联关系**

输出格式（含 Mermaid ER 图）见 [references/output-templates.md#step-2](references/output-templates.md)。

---

## Step 3: 业务流程梳理

### 3.1 识别业务入口

按项目类型定位，详见 [references/language-hints.md](references/language-hints.md) 的"业务入口"小节。

涵盖：REST API、GraphQL、消息队列消费、定时任务、事件处理、gRPC。

### 3.2 追踪业务流程

对每个主要业务场景：
1. 从入口点开始（Controller / Handler）
2. 追踪 Service 层调用
3. 识别数据访问层（Repository / DAO / ORM）
4. 记录外部调用（第三方 API、消息队列）
5. 标注事务边界和异常处理

### 3.3 绘制流程图

使用 Mermaid `sequenceDiagram` 或 `stateDiagram-v2`。

输出格式见 [references/output-templates.md#step-3](references/output-templates.md)。

---

## Step 4: 架构结构分析

### 4.1 扫描目录结构

优先使用 `Glob` 或等价工具按深度列出源码目录（深度 2-3 层），跳过 `node_modules`、`target`、`build`、`dist`、`.git`、`vendor` 等无关目录。

需要可视化目录树时可调用 `tree -L 3 -I 'node_modules|target|build|dist'`（需确认环境已安装）。

### 4.2 识别架构模式

从目录命名 + 包结构 + 关键注解推断：
- **分层架构**: Controller → Service → Repository
- **六边形架构**: Domain → Application → Infrastructure / Adapter
- **微服务架构**: 多个独立服务（顶层 `services/` 或 monorepo）
- **模块化单体**: 按业务域划分模块

### 4.3 分析代码组织

记录包/模块职责划分、公共组件、配置管理方式、测试代码组织。

输出格式见 [references/output-templates.md#step-4](references/output-templates.md)。

---

## Step 5: 依赖关系整理

### 5.1 从构建文件提取依赖

按项目类型读取对应文件（见 [references/language-hints.md](references/language-hints.md) 的"依赖来源"）。

### 5.2 分类依赖

按用途分组：核心框架、数据存储、缓存、消息队列、工具库、开发和测试。

### 5.3 识别外部服务

从配置文件和代码查找：第三方 API、云服务（AWS / 阿里云等）、支付网关、短信/邮件服务。每项标注配置 key 前缀和调用文件位置。

输出格式（含依赖表格）见 [references/output-templates.md#step-5](references/output-templates.md)。

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
| 核心领域模型 | 实体类代码 + 注解 | 略过该实体的对应字段 |
| 业务流程 | Controller + Service 调用链 | 只画能追踪到的部分，标注 `[部分流程未覆盖]` |
| 项目结构 | 目录扫描 | 客观陈述，无需推断 |
| 外部依赖 | 构建文件 + 配置文件 | 无则不列 |
| **部署说明 - 环境要求** | 构建文件、`Dockerfile`、`docker-compose.yml`、CI 配置 | 未声明组件写 `待补充` |
| **部署说明 - 启动步骤** | `README`、`Makefile`、`package.json scripts`、`Dockerfile CMD`、CI workflow | 找不到则写 `待补充（未在代码库中发现启动脚本）` |
| **部署说明 - 配置说明** | `application-example.yml`、`.env.example`、配置类 | 不要编造配置项 |
| **开发指南** | `CONTRIBUTING.md`、`.editorconfig`、lint 配置、git hooks、`CODEOWNERS` | 找不到则整节写 `待补充（建议人工编写）` |

### 6.2 组装文档

按 [references/output-templates.md#step-6](references/output-templates.md) 的完整骨架组装，务必在头部写入机器可读锚点：

```markdown
<!-- DOC_META: last_commit=<HEAD commit>, generated=<当前日期> -->
```

### 6.3 保存文档

保存到 `docs/PROJECT_DOCUMENTATION.md`（推荐），或项目根目录的 `DOCUMENTATION.md`。

如果文档规模较大（估计 > 1500 行），采用**拆分输出**：
- `docs/PROJECT_DOCUMENTATION.md` — 总览、目录索引
- `docs/domain-model.md`、`docs/business-flows.md`、`docs/architecture.md`、`docs/dependencies.md` — 分节详情

### 6.4 生成摘要

给用户一段简短摘要：核心功能、主要技术栈、业务流程数量、核心实体数量、文档保存位置。

---

## Step 7: 输出质量自检（必做）

生成后逐项确认：

- [ ] 所有章节都有实质内容或明确标注「待补充」，没有空壳占位
- [ ] 头部已写入 `<!-- DOC_META: ... -->` 锚点
- [ ] Mermaid 图表语法正确（可用在线 Mermaid Live Editor 验证）
- [ ] 重要断言标注了来源文件
- [ ] 专业术语使用一致
- [ ] 中英文混排时有适当空格
- [ ] 没有出现示例模板中的虚构值（如 `Spring Boot 2.7.5`、`连续登录失败 5 次锁定`）被当作当前项目事实写入

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

> 100 文件的项目：

1. **优先分析核心模块**（`core/`、`domain/`、`service/`）
2. **采样分析**：每个模块 2-3 个代表性文件
3. **渐进式文档**：先生成框架，再逐步填充
4. **并行派发子 agent**（Claude Code 用 `Agent`，其他平台用等价 dispatch；无此能力则顺序执行）

   示例：
   ```
   子任务 1: 分析用户模块（entity/User*, service/User*, controller/User*）
   子任务 2: 分析订单模块（entity/Order*, service/Order*, controller/Order*）
   子任务 3: 分析支付模块（entity/Payment*, service/Payment*, client/*Pay*）
   ```
   每个子任务输出结构化结果（领域模型片段 + 业务流程片段），主 agent 汇总去重。

Monorepo 处理策略见 [references/language-hints.md#monorepo](references/language-hints.md)。

---

## 最佳实践

1. **保持客观**: 基于代码事实，避免主观评价
2. **使用图表**: 复杂关系用 Mermaid 展示
3. **提供上下文**: 不仅说"是什么"，还要说"为什么"（如果代码注释或 commit 里有）
4. **标注来源**: 重要信息标注来源文件
5. **宁缺毋滥**: 找不到来源就写「待补充」，不要用示例值填充
