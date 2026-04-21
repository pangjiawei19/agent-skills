# Project Documentation Generator

从代码库自动生成全面项目文档的 skill。

## 何时使用

- ✅ 新接手项目，需要快速建立整体认知
- ✅ 项目缺少文档或文档严重过时
- ✅ 团队新成员入职，需要 onboarding 材料
- ✅ 代码重构后，需要更新文档（支持增量更新模式）

## 输出内容

生成**两层文档结构**：项目层 + 领域层。

```
docs/
├── project-overview/          # 项目层（非业务内容）
│   ├── README.md              # DOC_META + DOMAIN_MAP + 项目背景 + 技术栈 + 核心功能 + 域索引
│   ├── architecture.md        # 架构模式、系统架构图、目录结构、领域划分、跨域 ER
│   ├── milestones.md          # 里程碑（历史 + 未来）
│   ├── dependencies.md        # 外部依赖
│   ├── deployment.md          # 部署说明
│   └── development.md         # 开发指南
└── domains/                   # 领域层（所有业务内容）
    ├── README.md              # 领域清单
    └── <domain>/              # 每个业务域一个子目录
        ├── README.md          # 领域概览 + 对外接口
        ├── domain-model.md    # 本域所有实体
        └── flows.md           # 本域所有流程
        # 小域可退化为单 README.md
```

**为什么这样设计**：业务内容全部聚合到 `domains/`，每个域自包含。跨域关系通过链接表达而不是抽共性到全局层——心智模型简单、增量更新无歧义、每次业务改动只影响一个 `domains/<x>/`。

**单领域项目**自动退化为无 `domains/` 的平铺结构。

完整格式示例见 [example-output.md](example-output.md)（⚠️ 虚构示例 + 单文件合并展示；实际产出会按领域拆到 `domains/`）。

## 支持的项目类型

Java / Spring、Node.js / Express / NestJS、Python / Django / Flask / FastAPI、Go、Rust，以及 Monorepo 结构。各语言的详细定位提示见 [references/language-hints.md](references/language-hints.md)。

## 跨 Agent 平台使用

本 skill 主文件使用 Claude Code 工具名。在 Copilot CLI、Codex、Gemini CLI、自建 Agent SDK 等平台运行时，请参考 [references/tool-mapping.md](references/tool-mapping.md) 做工具等价替换。

## 文件清单

| 文件 | 作用 |
|------|------|
| `SKILL.md` | 主流程（Step 0-7） |
| `references/output-templates.md` | 各 Step 的 markdown / Mermaid 输出样板 |
| `references/language-hints.md` | 按语言/框架的实体、入口、依赖定位提示 |
| `references/tool-mapping.md` | 跨 Agent 平台工具映射表 |
| `example-output.md` | 完整文档示例（虚构） |

## 生成后的人工补充

AI 能准确提取代码事实，但以下内容需要人工补充（skill 中会标注「待补充」）：

1. **业务背景** — 为什么做这个项目？解决什么问题？
2. **架构决策** — 为什么选这个技术栈？有哪些权衡？
3. **已知问题** — 技术债务和待优化点
4. **性能指标** — QPS、响应时间等关键指标
5. **安全考虑** — 安全机制和注意事项

## 常见问题

### 生成的文档不准确怎么办？

skill 严格遵循"数据来源原则"（SKILL.md Step 6.0）：只写能从代码/配置读出的内容，找不到来源的写「待补充」。如果仍出现不准确：

- 检查代码注释和命名是否能反映业务含义
- 在 prompt 中补充业务背景，让 AI 基于更多上下文推断
- 让 AI 重新生成（在调用时说"重新生成"可跳过增量更新）

### 可以自定义文档模板吗？

可以。修改 `references/output-templates.md` 调整输出格式，或修改 `SKILL.md` 调整流程。

### 支持生成英文文档吗？

默认生成中文。需要英文时在调用中明确：`Generate project documentation in English`。

### 大型项目（1000+ 文件）如何处理？

skill 采用采样分析 + 并行子 agent 策略（SKILL.md "处理大型项目"小节）：筛选核心实体（≤15 个）和主要流程（≤8 个）详述，其余用精简表格罗列。

### 增量更新是怎么判断的？

skill 在 `docs/project-overview/README.md` 头部写入两个锚点：
- `<!-- DOC_META: last_commit=... -->` — 上次生成的 commit
- `<!-- DOMAIN_MAP ... -->` — 代码路径到业务域的映射（YAML）

下次运行时对比 git diff，按变更规模（<10% / 10-30% / >30%）决定是否全量；增量模式下把变更文件按 DOMAIN_MAP 分桶到对应领域，只重扫受影响的文档文件。详见 SKILL.md Step 0。

### 领域是怎么划分的？

首次生成时 skill 会：
1. 按语言启发式推断（Java 按 package、Node.js 按顶层模块、Monorepo 按 service 等）
2. 输出推断结果给用户 review（表格形式：域名 / 推断依据 / 覆盖 paths / 核心实体）
3. **硬停等用户确认或修改**后写入 DOMAIN_MAP，再继续生成

之后增量更新都以 DOMAIN_MAP 为准，不会重新推断。如需调整领域划分，手动编辑 `project-overview/README.md` 头部的 DOMAIN_MAP 即可。

### 项目层和领域层怎么切分？

**项目层**只放非业务的项目级内容（架构、依赖、部署、开发约定）。**所有业务内容都在 `domains/`**。

归属规则（skill 自动执行，防止同一事实在多个域重复）：

- **实体**：每个实体归属且仅归属一个域（定义文件路径命中哪个域 paths 就归哪个域）。被其他域引用时用链接 `../<owning-domain>/domain-model.md#xxx`，不复述字段。
- **流程**：
  - 同步调用链 → 归**发起方**（入口 Controller 所在域）
  - 事件驱动 → 归**消费方**（业务动作发生处）
  - 纯编排（Saga/工作流）→ 归**编排代码所在域**
- **反向索引**：被其他域流程调用的接口，在本域 `flows.md` 末尾列表格指向调用方域的流程，不复述流程内容。

### 项目不是 git 仓库怎么办？

skill 会自动检测（`git rev-parse --is-inside-work-tree`），非 git 仓库强制走全量生成，DOC_META 中 `last_commit` 填 `none`。

### 里程碑从哪来？

- **历史里程碑**：优先从 `git tag --sort=-creatordate` 提取，其次从 `CHANGELOG.md` 的版本节提取；两者都没有时 `milestones.md` 仍生成，但整块写"待补充"引导人工填写
- **未来里程碑**：AI 推不出，整块留"待补充"

### 系统架构图画到什么程度？

从依赖和配置能准确识别的组件（数据库、MQ、主要第三方 SDK）都会画；推不出的组件（网关、CDN、负载均衡——通常在部署层而非代码层）**不画**，只在组件清单表里标"待补充"。详见 [references/language-hints.md](references/language-hints.md) 的"架构组件识别"小节。

## 贡献

- 修改 `SKILL.md` 优化分析流程
- 在 `references/language-hints.md` 添加更多语言/框架的定位提示
- 在 `references/output-templates.md` 补充输出格式

## 许可

MIT License
