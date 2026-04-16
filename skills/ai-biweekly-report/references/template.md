# AI 工程半月报 — 输出格式示例

以下是最终生成文档的格式参考。agent 执行时按此格式填充实际内容。

---

## 飞书文档示例

```markdown
# AI 工程半月报 | 2026 年 4 月上旬

**时间范围**：2026-04-01 ~ 2026-04-15
**受众定位**：后端工程师转型 AI Engineer
**分析视角**：工程可行性、API 调用、系统架构

---

## 本期趋势

### 趋势一：API 调用成本进入新一轮降价周期

多家厂商同时降价（OpenAI GPT-5 Turbo 降 50%、Google Gemini 2.5 降 40%），模型能力提升的同时成本大幅下降。Self-host vs API 的决策平衡点正在改变。

**支撑资讯**：#1 GPT-5 Turbo、#3 Gemini 2.5 Pro 降价
**行动建议**：重新评估现有 self-host 模型的 ROI，对比最新 API 价格。成本敏感型应用优先切换到新 API。

### 趋势二：Agent 编排从链式调用向状态图演进

LangGraph v2.0 和 CrewAI 0.5 都在向状态图模式迁移，支持条件分支、暂停恢复和人机协作。这意味着 Agent 应用正在从简单 demo 走向生产级复杂度。

**支撑资讯**：#6 LangGraph v2.0、#7 CrewAI 0.5
**行动建议**：如果团队在做 Agent 项目，值得花一个周末学习 LangGraph v2 的状态图设计。已有 LangChain 项目的评估迁移成本。

---

## 资讯速览

| 序号 | 标题 | 一句话价值判断 | 上手门槛 | 链接 |
|------|------|---------------|---------|------|
| 1 | GPT-5 Turbo API 发布 | 成本降 50%，256K context，直接替换 GPT-4 | 周末可试 | https://openai.com/blog/gpt-5-turbo |
| 2 | Mamba-3 架构论文 | 推理速度 4x，Transformer 替代方向 | 长期关注 | https://arxiv.org/abs/2026.xxxxx |
| 3 | Gemini 2.5 Pro 降价 40% | 多模态能力提升，价格更有竞争力 | 周末可试 | https://blog.google/gemini-2-5 |
| 4 | vLLM 0.8 发布 | 推理吞吐量提升 2x，支持 speculative decoding | 需要基础 | https://github.com/vllm-project/vllm |
| 5 | Anthropic Tool Use 新增 streaming | Agent 场景延迟降低，支持流式工具调用 | 周末可试 | https://docs.anthropic.com/tool-use |
| 6 | LangGraph v2.0 | Agent 编排新范式，状态图 + checkpoint | 需要基础 | https://github.com/langchain-ai/langgraph |
| 7 | CrewAI 0.5 发布 | 多 Agent 协作框架，简化编排复杂度 | 周末可试 | https://github.com/crewAIInc/crewAI |
| 8 | Uber 发布 RAG 生产实践 | 大规模 RAG 管线的工程经验，含踩坑总结 | 需要基础 | https://eng.uber.com/rag-production |
| 9 | Braintrust 开源评估框架 | LLM 输出评估标准化，支持 CI 集成 | 周末可试 | https://github.com/braintrustdata/autoevals |
| 10 | RAFT 论文：检索增强微调 | 结合 RAG 和微调，小模型也能做复杂任务 | 长期关注 | https://arxiv.org/abs/2026.yyyyy |

---

## 重点深度分析

### [1] GPT-5 Turbo API 发布，成本降低 50%

**来源**：OpenAI Blog | 2026-04-10
**原文链接**：https://openai.com/blog/gpt-5-turbo
**上手门槛**：周末可试

- **核心情报 (What)**：GPT-5 Turbo 开放 API，input $2/M tokens，output $6/M tokens，支持 256K context window

- **技术原理解析 (How)**：
  - 基于 MoE 架构优化，活跃参数量降低但效果持平
  - 新增 structured output 模式，JSON schema 约束输出
  - function calling 延迟降低 30%

- **应用场景 (Where)**：
  - 直接替换 GPT-4 调用，成本减半
  - 长上下文 RAG 管线的模型层替换
  - structured output 可简化后处理代码

- **工程化价值 (Why)**：
  - 建议立即评估迁移，ROI 明显
  - 注意 rate limit 变化和 API 兼容性
  - 256K context 可能改变 chunking 策略

---

### [6] LangGraph v2.0 发布，Agent 编排新范式

**来源**：GitHub | 2026-04-08
**原文链接**：https://github.com/langchain-ai/langgraph
**上手门槛**：需要基础

- **核心情报 (What)**：LangGraph v2.0 引入基于状态图的 Agent 编排，支持持久化和人机协作

- **技术原理解析 (How)**：
  - 状态图替代链式调用，支持条件分支和循环
  - 内置 checkpoint 机制，支持 Agent 暂停/恢复
  - 与 LangSmith 深度集成，可观测性大幅提升

- **应用场景 (Where)**：
  - 复杂多步骤 Agent 工作流
  - 需要人工审核节点的自动化流程

- **工程化价值 (Why)**：
  - 值得 Clone 学习其状态管理设计
  - 如已用 LangChain，建议评估迁移
  - 注意 v1 → v2 有 breaking changes

---

### [8] Uber 发布大规模 RAG 生产实践

**来源**：Uber Engineering Blog | 2026-04-12
**原文链接**：https://eng.uber.com/rag-production
**上手门槛**：需要基础

- **核心情报 (What)**：Uber 分享其内部 RAG 系统从 PoC 到生产的完整历程，日处理 200M+ 查询

- **技术原理解析 (How)**：
  - 混合检索（BM25 + 向量）比纯向量检索 recall 提升 15%
  - 分层缓存设计：热点 query 缓存命中率 85%
  - embedding 模型蒸馏：延迟降低 4x，效果损失 <2%

- **应用场景 (Where)**：
  - 任何从 RAG demo 走向生产的团队
  - 高 QPS 场景的缓存和性能优化

- **工程化价值 (Why)**：
  - 提供了从 demo 到生产的具体 checklist
  - 缓存层设计思路可直接借鉴
  - 注意其技术栈假设（K8s + 自建 embedding service）

---

## 附录：全部链接汇总

- [GPT-5 Turbo API](https://openai.com/blog/gpt-5-turbo)
- [Mamba-3 论文](https://arxiv.org/abs/2026.xxxxx)
- [Gemini 2.5 Pro](https://blog.google/gemini-2-5)
- [vLLM 0.8](https://github.com/vllm-project/vllm)
- [Anthropic Tool Use Streaming](https://docs.anthropic.com/tool-use)
- [LangGraph v2.0](https://github.com/langchain-ai/langgraph)
- [CrewAI 0.5](https://github.com/crewAIInc/crewAI)
- [Uber RAG 实践](https://eng.uber.com/rag-production)
- [Braintrust Autoevals](https://github.com/braintrustdata/autoevals)
- [RAFT 论文](https://arxiv.org/abs/2026.yyyyy)

---

*本报告由小虾米生成 | 报告周期：2026-04-01 ~ 2026-04-15 | 下次更新：2026-05-01*
```

---

## 消息摘要示例

```markdown
## AI 工程半月报已完成（2026-04-01 ~ 2026-04-15）

**完整文档**：https://www.feishu.cn/docx/xxxxx

### 本期趋势
1. API 调用成本进入新一轮降价周期 → 重新评估 self-host vs API
2. Agent 编排从链式调用向状态图演进 → 学习 LangGraph v2 状态图设计

### 资讯速览（10 条）
1. GPT-5 Turbo API — 成本降 50% `周末可试`
2. Mamba-3 架构 — 推理 4x 加速 `长期关注`
3. Gemini 2.5 Pro 降价 — 多模态更便宜 `周末可试`
4. vLLM 0.8 — 推理吞吐 2x `需要基础`
5. Anthropic Tool Use Streaming `周末可试`
6. LangGraph v2.0 — Agent 状态图 `需要基础`
7. CrewAI 0.5 — 多 Agent 协作 `周末可试`
8. Uber RAG 生产实践 `需要基础`
9. Braintrust 评估框架 `周末可试`
10. RAFT 检索增强微调 `长期关注`
```
