# Project Documentation Generator

从代码库自动生成全面项目文档的 skill。

## 何时使用

- ✅ 新接手项目，需要快速建立整体认知
- ✅ 项目缺少文档或文档严重过时
- ✅ 团队新成员入职，需要 onboarding 材料
- ✅ 代码重构后，需要更新文档（支持增量更新模式）

## 输出内容

生成 `docs/PROJECT_DOCUMENTATION.md`，包含：

- 项目简介、领域模型（Mermaid ER 图）、业务流程（序列图/状态机）、项目结构、外部依赖、部署说明、开发指南

完整结构和格式见 [example-output.md](example-output.md)（⚠️ 虚构示例，仅示意格式）。

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

skill 自动采用采样分析 + 并行子 agent 策略（SKILL.md "处理大型项目"小节）。超过 1500 行预估输出时会拆分为 `overview.md` + `domain-model.md` + `business-flows.md` 等多文件。

### 增量更新是怎么判断的？

skill 在文档头部写入 `<!-- DOC_META: last_commit=... -->` 锚点。下次运行时对比 git diff，按变更规模和结构性信号决定增量或全量重生成，详见 SKILL.md Step 0。

## 贡献

- 修改 `SKILL.md` 优化分析流程
- 在 `references/language-hints.md` 添加更多语言/框架的定位提示
- 在 `references/output-templates.md` 补充输出格式

## 许可

MIT License
