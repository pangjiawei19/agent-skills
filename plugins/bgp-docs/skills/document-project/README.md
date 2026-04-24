# Project Documentation Generator

从代码库生成**两层项目文档**（项目层 + 领域层）的 skill。

## 何时使用

- ✅ 新接手项目，需要快速建立整体认知（**首次模式**：全量生成）
- ✅ 团队新成员入职，需要 onboarding 材料
- ✅ 新增/改动功能后更新文档（**增量模式**：只重算代码可提取部分，人工补充的内容保留）
- ✅ 代码重构后同步文档

skill 会自动判断模式：检测到 `docs/wiki/` 已存在时走增量模式，否则走首次模式。

## 输出结构

```
docs/wiki/
├── README.md              # 项目层入口：项目背景 + 技术栈 + 核心功能 + 域索引
├── 01-architecture.md     # 架构模式、系统架构图、目录结构、领域划分、跨域 ER
├── 02-milestones.md       # 里程碑（历史 + 未来）
├── 03-dependencies.md     # 外部依赖
├── 04-deployment.md       # 部署说明
├── 05-development.md      # 开发指南
└── domains/               # 领域层（业务内容）
    ├── README.md          # 领域清单
    └── <domain>/          # 每个业务域一个子目录
        ├── README.md          # 领域概览 + 对外接口（含跳转段）
        ├── domain-model.md    # 本域所有实体（拆分模式）
        └── flows.md           # 本域所有流程（拆分模式）
        # 小域退化为单 README.md（默认）
```

**为什么这样设计**：业务内容全部聚合到 `docs/wiki/domains/`，每个域自包含；跨域关系通过链接表达而不是抽共性到全局层——心智模型简单、每次业务改动只影响一个 `domains/<x>/`。

## 两层叠加：代码层 vs 人工层

文档由两层组成，增量更新时 skill 只碰代码层：

| 层 | 边界 | 行为 |
|---|------|------|
| **代码层**（auto 区） | `<!-- auto:xxx -->...<!-- /auto:xxx -->` 包裹的块 | 每次重跑从代码完整重算 |
| **人工层** | auto 标记之外的所有内容 | 永不改写 |

比如 Order 实体的字段清单在 `auto:entity:Order` 里，代码改动时会自动更新；而紧跟其后的"业务背景 / 例外情况"小节是人工写的，`30 分钟为什么是 30 分钟`、`大客户特批规则`这类解释永远不会被覆盖。

**边界划分原则**：代码里能直接验证的事实（字段、关联、校验规则、调度规则、状态机边）放 auto 区；"为什么这样设计 / 业务背景 / 例外情况 / 性能目标"放人工区。

**单领域项目**：skill 会建议使用单页文档而不是两层结构；若用户确认继续，退化为扁平的 `docs/wiki/{README,domain-model,flows}.md`。

## 支持的项目类型

Java / Spring、Node.js / Express / NestJS、Python / Django / Flask / FastAPI、Go、Rust、Monorepo。各语言的详细定位提示见 [references/language-hints.md](references/language-hints.md)。

## 跨 Agent 平台使用

本 skill 主文件使用 Claude Code 工具名（`Glob`、`Grep`、`Read`、`Bash`、`Agent`）。在其他 Agent 平台运行时参见 [references/tool-mapping.md](references/tool-mapping.md)。

## 文件清单

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 主流程（Step 1-8） |
| `references/output-templates.md` | 两层文档骨架模板 |
| `references/language-hints.md` | 按语言/框架的实体、入口、依赖定位提示 |
| `references/tool-mapping.md` | 跨 Agent 平台工具映射 |

## 核心原则

### 数据来源

**只写能从代码/配置读出的内容，找不到写"待补充"**。详见 SKILL.md 全局原则。

### 归属规则（防止同一事实在多个域重复）

- **实体**：每个实体归属且仅归属一个域（定义文件路径命中哪个域 paths 就归哪个域）。被其他域引用时用链接，不复述字段
- **流程**：
  - 同步调用链 → 归**发起方**
  - 事件驱动 → 归**消费方**
  - 纯编排（Saga/工作流）→ 归**编排代码所在域**
- **共享基础设施**（shared-lib、util）不作业务域，只在 01-architecture.md 提一下

### 跨域链接统一写法

所有跨域链接**统一指向 `../<other-domain>/README.md#<anchor>`**。拆分模式下 README.md 保留跳转段，锚点始终可达——避免"单文件 vs 拆分"切换时要改所有引用方。

## 生成后的人工补充

AI 能准确提取代码事实，但以下内容需要人工补充（skill 会标注"待补充"）：

1. **业务背景** — 为什么做这个项目？解决什么问题？
2. **架构决策** — 为什么选这个技术栈？有哪些权衡？
3. **已知问题** — 技术债务和待优化点
4. **性能指标** — QPS、响应时间等关键指标
5. **安全考虑** — 安全机制和注意事项

## 常见问题

### 生成的文档不准确怎么办？

skill 严格遵循"数据来源原则"：只写能从代码/配置读出的内容。若仍不准：

- 检查代码注释和命名是否能反映业务含义
- 在 prompt 中补充业务背景，让 AI 基于更多上下文推断
- 修改 auto 区外的人工层（业务背景、设计说明等）——skill 重跑时会保留

### 如何更新文档？

**直接重跑 skill**。检测到 `docs/wiki/` 已存在会自动走增量模式：

- auto 区（字段清单、流程序列图、依赖表、架构图等）按当前代码重算
- 人工层（业务背景、设计说明、已填写的"待补充"、对领域表的手动调整等）原样保留
- 新增的实体/流程会作为新 auto 块追加到对应域文件的合适位置
- 代码里删掉的实体/流程 → 对应 auto 块内容变空，skill 不删节标题、不清理人工层——你看到空块自己决定是否清理

### 什么内容放哪里？

- **放 auto 区**：实体字段、关联关系、校验/调度/状态机里能提取的规则、序列图、依赖版本、架构组件 — 代码里都能找到
- **放人工层**（auto 区之外的 prose）：业务背景、设计决策的原因、例外情况、性能目标、架构演进历史 — 代码里推不出

直接在 auto 块内手写的内容**会被重跑覆盖**——要补充背景请写在 auto 块之外。

### 领域划分怎么调整？

直接编辑 `01-architecture.md` 的 `auto:domains-table` 块 + 对应 `domains/<x>/` 目录即可。skill 重跑时**行级既有权威**：既有行连同你加的备注一起保留，只在代码出现未归属的新路径时追加"待归属"行让你决定。

### 想给一个域重命名（如 `exchange-rate` → `fx-rate`）？

skill **不做自动重命名**（涉及物理 `mv` 和链接重写，风险高）。需要手动同步 4 处：

1. `docs/wiki/01-architecture.md` 的 `auto:domains-table` 行里改域名
2. `docs/wiki/README.md` 的 `auto:domain-index` — 下次跑 skill 会跟随 domains-table 自动更新**文本**，但**链接 URL** 不会变
3. `docs/wiki/domains/README.md` 的 `auto:domains-listing` — 同上
4. 物理目录：`git mv docs/wiki/domains/<old>/ docs/wiki/domains/<new>/` 并 sed 批量替换文档里的旧路径引用

完成 1 后重跑 skill，2/3 的文本会自动同步；4 属于一次性手工操作。

### 大型项目（1000+ 文件）如何处理？

skill 采用采样 + 并行子 agent 策略（SKILL.md "处理大型项目"小节）：每域核心实体 ≤ 10 个、每域主要流程 ≤ 5 个，其余精简表格罗列。

### 项目不是 git 仓库怎么办？

里程碑数据源（`git tag` / `CHANGELOG`）推不出时写"待补充"；其他内容不受影响。

### 系统架构图画到什么程度？

从依赖和配置能准确识别的组件（数据库、MQ、主要第三方 SDK）都会画；推不出的组件（网关、CDN、负载均衡等部署层组件）**不画**，只在组件清单表里标"待补充"。详见 [references/language-hints.md](references/language-hints.md) 的"架构组件识别"小节。

## 贡献

- 修改 `SKILL.md` 优化分析流程
- 在 `references/language-hints.md` 添加更多语言/框架的定位提示
- 在 `references/output-templates.md` 补充输出格式

## 许可

MIT License
