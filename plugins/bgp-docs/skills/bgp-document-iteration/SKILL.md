---
name: bgp-document-iteration
description: 当用户完成一轮 feature 分支开发、准备合并回 develop/main 之前,需要把本次迭代做了什么记录成一份结构化文档时使用。典型请求包括:"生成迭代文档"、"记录这次开发"、"本次改动整理一下"、"把这次 feature 做的事情记下来"、"/bgp-document-iteration"。
---

# BGP Document Iteration

基于 git diff 生成一份"本次迭代做了什么"的文档,用于 feature 分支合并前的存档。

## Scope 边界(重要,先读)

本 skill 只生成**事实层**内容,不生成**决策层**内容:

| 能生成(从 git 可读) | 不生成(git 里没有) |
|---|---|
| 改了哪些文件、哪些 domain | 为什么这么做 |
| 新增/修改/删除的关键实体、接口 | 考虑过哪些其他方案 |
| 按 commit 的改动叙事 | 为什么最终选了这个 |
| 统计数据(commit 数、行数) | 有哪些遗留问题 |

**定位**:结构化 changelog,不是完整决策文档。决策层内容由用户在生成后手动补充(文档里已留小节)。

## 输出路径

```
docs/wiki/iterations/YYYY-MM-DD-<branch-slug>.md
```

- `YYYY-MM-DD`: 执行当天日期
- `<branch-slug>`: 当前分支名去掉 `feature/`、`feat/`、`bugfix/` 等前缀,剩余部分的 `/` 替换为 `-`
  - 例:`feature/pay/alipay` → `pay-alipay`
- 同名已存在则追加 `-2`、`-3`,不覆盖既有文件

## 不适用场景

执行前检查,命中任一条件 → 告知用户并终止:

- 当前目录不是 git 仓库
- 当前分支是 `main` / `master` / `develop`(主干分支上不该走这个流程)——除非用户明确确认继续
- 指定 diff 范围内 commit 数为 0

---

## Step 1: 前置检查

并行执行:

```bash
git rev-parse --is-inside-work-tree
git branch --show-current
git log --oneline -20
```

- 非 git 仓库 → 终止
- 分支是 main/master/develop → 警告并询问用户是否继续
- 记录当前分支名,供后续命名和文档使用

## Step 2: 确定 diff 起点

**自动检测默认 base**(按优先级):

1. `git rev-parse --verify develop` 成功 → 默认 base = `develop`
2. 否则 `git rev-parse --verify main` 成功 → 默认 base = `main`
3. 否则 `git rev-parse --verify master` 成功 → 默认 base = `master`
4. 都没有 → 无默认,必须用户指定

展示给用户:
- 默认 base(如上检测结果)
- `git log <base>..HEAD --oneline` 的 commit 清单(让用户直观看到会包含哪些 commit)

**询问**:

> 默认起点:`<base>`(共 N 个 commits 将被纳入)。是否使用?
> - 回复 `y` 使用默认
> - 回复 commit hash 或分支名以指定其他起点
> - 回复 `<from>..<to>` 指定区间

把用户确认的起点转为 `<base>..HEAD` 或 `<from>..<to>` 形式,记为 `<range>`。

## Step 3: 询问文档主题(可选)

默认用 `<branch-slug>` 作标题。询问用户:

> 文档标题默认为 `<branch-slug>`,是否需要改成更可读的标题?回复新标题或 `n` 使用默认。

用户输入作为文档 H1 标题。

## Step 4: 收集 git 数据

并行执行:

```bash
git log <range> --pretty=format:'%h|%ai|%an|%s'
git log <range> --pretty=format:'%h%n%B%n---COMMIT-END---'  # 含 body
git diff <range> --stat
git diff <range> --name-status
```

**大小控制**:

- 如果 `--stat` 显示总变动 > 3000 行,**不读完整 diff**——按文件挑选变动最大的 5-10 个 `git diff <range> -- <file>` 逐个读
- 目的:避免 context 爆掉,以关键文件为主

## Step 5: 按 domain 归属改动文件

**优先级**:

1. **读既有架构文档**:`docs/wiki/01-architecture.md` 是否存在
   - 存在 → 提取 `<!-- auto:domains-table -->` 块中每行的"paths"列
   - 对每个改动文件路径,匹配第一个命中的 path prefix,归属该域
2. **启发式推断**(无架构文档时):
   - 按 `src/<name>/` / `modules/<name>/` / `services/<name>/` 的首层目录名
   - Java 按 package 第一段:`com.xxx.<domain>.*`
3. **推不出的文件** → 归入"其他 / 未归属"组

## Step 6: 生成文档

按下方模板写入 `docs/wiki/iterations/<filename>.md`。

**每个 domain 下的写作规则**:

- **关键改动**(详述,3-10 条):挑选变动行数大、新增文件、删除文件、或从 commit message 可判断为核心的改动
  - 每条一行,格式:`- [A/M/D] <file-path>:<一句话说明>`
  - 说明**只基于 diff 和 commit message 能确认的事实**,不虚构意图
- **文件清单**(简列,其余都进这里):
  - 格式:`- A path/to/file.ext`(字母为 A/M/D/R)
  - 超过 20 个时可合并同目录

### 文档模板

```markdown
# <标题>

- 日期: YYYY-MM-DD
- 分支: `<branch-name>`
- Diff 范围: `<range>`
- 统计: N commits, X 文件, +Y/-Z 行
- 涉及 domain: <domain-a>, <domain-b>, ...

## 改动摘要

<一段 3-8 句叙事,按 commit 顺序串起本次迭代做了什么。
材料来源:commit subject + body。
要求:用业务视角叙述(如"实现 XX 登录"),不是技术动作清单(如"添加了 LoginService.java")。>

## 详细改动

### <domain A>

**关键改动**:
- [A] `src/login/LoginService.java`:新增 SSO 登录入口
- [M] `src/user/User.java`:User 实体增加 `ssoId` 字段
- [D] `src/login/OldAuthFilter.java`:移除旧认证过滤器

**文件清单**(共 N 个):
- A src/login/SsoClient.java
- M src/login/config/LoginConfig.java
- ...

### <domain B>

...

### 其他 / 未归属

- M README.md
- M pom.xml

## Commits

- `abc1234` <subject>(<author>, YYYY-MM-DD)
- `def5678` <subject>(<author>, YYYY-MM-DD)
- ...

---

## 决策补充(人工填写)

> 以下内容 git diff 里读不出,需要手动补充。保留空小节作为提示。

### 背景 / 目标

<这次迭代为什么要做?解决什么问题?>

### 方案对比 / 选型理由

<考虑过哪些方案?为什么选现在这个?>

### 遗留问题 / 下一步

<有什么已知没处理的?后续要做什么?>

### 相关链接

<issue / 需求文档 / 讨论记录的链接>

---

**后续建议**:本次改动涉及的 domain 现状文档如需同步,运行 `document-project` skill。
```

## Step 7: 询问是否 commit

生成文件后,告知用户路径并询问:

> 已生成 `docs/wiki/iterations/<filename>.md`(N 行)。
> 是否 commit 到当前分支 `<branch-name>`?回复 `y` / `n`。

- `y` → 执行:
  ```bash
  git add docs/wiki/iterations/<filename>.md
  git commit -m "docs: 添加 <branch-slug> 迭代文档"
  ```
- `n` → 不做任何 git 操作,结束

**不做的事**:
- 不执行 `git merge`
- 不执行 `git push`
- 不切换分支

合并操作由用户自己完成。

## Step 8: 自检

生成后执行:

1. **文件真的写入了**:`ls docs/wiki/iterations/<filename>.md` 存在且非空
2. **抽查路径真实性**:从"关键改动"小节随机抽 3 条,`ls` 验证路径存在(对 `[D]` 删除的跳过)
   - 抽查到虚构路径 → 修正为实际改动文件
3. **统计数字对得上**:文档顶部声明的 commit 数、文件数与 `git log --oneline <range> | wc -l` 和 `git diff <range> --name-only | wc -l` 一致
4. **commit 数 > 0**:如果 range 内没有 commit,说明范围给错了,回到 Step 2 重新询问

## 常见错误

| 错误 | 原因 | 修正 |
|---|---|---|
| 关键改动写了没改过的文件 | AI 从 commit message 脑补 | 只写 `--name-status` 里真出现的文件 |
| 改动摘要变成技术流水账 | 直接拷 commit subject | 按业务目标重新组织,一段叙事 |
| 未归属文件占了大头 | 架构文档的 paths 列写得太具体,没匹配上 | 降级用启发式(按 src 首层目录)兜底 |
| 文档已存在被覆盖 | 忘了检查 | 命名追加 `-2` / `-3` |
| diff 过大爆 context | 没做大小控制 | 按 Step 4 规则,超过 3000 行只挑关键文件 |
