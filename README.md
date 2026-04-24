# agent-skills

BGP 团队内部的 Claude Code agent skill 分发仓库,通过 Claude Code plugin marketplace 机制安装和更新。

## 安装

在 Claude Code 中:

```
/plugin marketplace add pangjiawei19/agent-skills
/plugin install bgp-docs@bgp-skills
```

后续更新:

```
/plugin marketplace update bgp-skills
```

## 包含的 Plugin

### `bgp-docs` — 项目文档套件

生成和维护项目文档的配套 skill:

| Skill | 用途 | 典型触发 |
|---|---|---|
| `document-project` | 从代码库生成两层项目文档(项目层 + 领域层) | 新接手项目、onboarding 材料、代码重构后同步 |
| `bgp-document-iteration` | 基于 git diff 生成本次迭代改动文档 | feature 分支合并 develop 前 |

**配套关系**:`document-project` 维护项目**现状**(随代码演进),`bgp-document-iteration` 记录每次**变更历史**(不可变时间线)。两者输出互不覆盖,通过链接串联。

调用格式:`/bgp-docs:document-project`、`/bgp-docs:bgp-document-iteration`。也可以让 Claude 自动根据任务描述触发。

## 目录结构

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json          # 分发清单
├── plugins/
│   └── bgp-docs/                 # 分发给团队的 plugin
│       ├── .claude-plugin/plugin.json
│       └── skills/
│           ├── document-project/
│           └── bgp-document-iteration/
└── skills/                       # 维护者本地使用的游离 skill(不参与分发)
    └── ...
```

## 开发者说明

**新增 skill 到既有 plugin**:

```bash
cd plugins/bgp-docs/skills/
# 创建 <skill-name>/SKILL.md
git add . && git commit -m "feat(bgp-docs): add <skill-name>"
```

**新增 plugin**:

1. 在 `plugins/` 下创建新目录 `<new-plugin>/`
2. 新建 `plugins/<new-plugin>/.claude-plugin/plugin.json`
3. 在 `.claude-plugin/marketplace.json` 的 `plugins` 数组里追加 entry
4. commit + push,团队成员 `/plugin marketplace update bgp-skills` 后可见

**游离 skill**:顶层 `skills/` 下的 skill 不进任何 plugin,仅供维护者本地使用(通过 symlink 到 `~/.claude/skills/`)。

## 验证

本地测试 plugin 可用性:

```
/plugin marketplace add ./agent-skills    # 添加本地 repo 作为 marketplace
/plugin install bgp-docs@bgp-skills
```

调用 `/bgp-docs:document-project` 能响应即为正常。
