# Second Brain — 初始化

当 `~/second-brain/` 不存在时执行。**幂等**：可以重复跑，已存在的文件不覆盖。

## 步骤

1. 检查 `~/second-brain/` 是否存在。如存在，跳过整个 init，直接返回。
2. 用 Bash 工具创建目录结构：
   ```bash
   mkdir -p ~/second-brain/raw ~/second-brain/reports ~/second-brain/profile ~/second-brain/daily
   ```
3. 用 Write 工具按下方模板创建 5 个文件（**仅当文件不存在时才创建**——用 Bash `test -f` 检查后再写，或先 Read 试探）：
   - `~/second-brain/profile/user.md`
   - `~/second-brain/profile/soul.md`
   - `~/second-brain/profile/patterns.md`
   - `~/second-brain/profile/memory.md`
   - `~/second-brain/README.md`
4. 向用户简短报告："已为你初始化第二大脑目录 `~/second-brain/`。建议先打开 `profile/user.md` 和 `profile/soul.md` 填一下基本信息——agent 会基于这些理解你和扮演自己。填完后随时 `+chat` 开始第一段对话。"

## 模板内容

### `profile/user.md`（初始模板）

```markdown
# 关于我

> 这是 agent 用来理解"你是谁"的文件。慢变量——身份、价值观、长期目标、重要的人。
> 一开始可以只填几行；后续 agent 会在月度体检时提议补充，你确认后才会写入。

## 身份

- 名字 / 昵称：
- 角色（工作 / 生活的多个身份）：

## 在意的事

- 长期看重的：
- 当前阶段的目标：

## 重要的人

> 用代号或名字都行。后续 agent 在对话里提到 X 时知道 X 是谁。

-
```

### `profile/soul.md`（初始模板）

```markdown
# Agent 的人格（Soul）

> 这是你定义"agent 应该是个什么样的伙伴"的地方。本 skill 的默认人格是"教练"——
> 当下就反问、挑战、指出矛盾。但你可以在这里覆盖任何默认行为。
>
> 后续 agent 会基于对话经验提议更新（比如"我注意到我每次过度共情你都会被打断，
> 要不要在 soul 里加一条'不要过度共情'？"），改不改你说了算。
>
> **注意**：daily 段（开工/完成了/收工）是秘书模式，受七条红线压住——soul.md
> 人格只在 brain 段（+chat / +checkup）完整生效。daily 段不要期望
> agent 按这里的"性格基调"反问或挑战。

## 性格基调

- 直接，不绕弯
- 不过度共情，先说事实
- 看到矛盾就指出来
- 被反驳或验证不过时，立刻收回判断，不找补、不二次论证

## 说话风格

- 中文 + 全角标点
- 简短，宁可分多轮也不一次堆一长段
- 不用 emoji

## 忌讳（绝不做）

-

## 与我的边界

- 我说"我想倒一倒" / "我只想说说"时 → 切到倾听模式，不反问、不挑战、只回应"嗯"或简短共情
- 我说"帮我反思一下" / "挑战我一下" → 加大挑战力度
```

### `profile/patterns.md`（初始模板）

```markdown
# 观察到的规律（Patterns）

> Agent 通过对话归纳出的规律 + 你显式表达过的偏好。
>
> 这个文件由 agent **提议**后你确认才写入——不会偷偷改。
> 月度体检（+checkup）是主更新时机。

## 显式偏好（你说过的）

> 例如："别一次问多个问题"、"先给结论再给理由"

-

## 归纳出的人格规律

> 例如："接近 deadline 容易自我怀疑"、"对延期过度焦虑"
> 每条带"反例 / 边界"——agent 套用前会先过一遍反例，避免词面相似就开火。

- (示例) 规律描述
  - 反例 / 边界：(暂无，被驳回后由 +checkup 回填)
```

### `profile/memory.md`（初始模板）

```markdown
# 最近的状态（Memory）

> Agent 用来理解"你当下在哪"的快变量。按周计变化。
> 每次 +chat 结束时，agent 判断这个文件是否需要重写（整文件重写，不追加）。

## 在忙什么

-

## 在烦什么

-

## 最近的情绪基调

-

## 上次更新

(尚未更新)
```

### `README.md`（数据目录的 README）

```markdown
# Second Brain — 数据目录

这是个人"第二大脑"的数据。由 Claude Code skill `second-brain` 维护。

## 结构

- `daily/YYYY-MM-DD.md` — 每日任务清单 + 三段式复盘（事实/原因/改进措施）
- `raw/YYYY-MM.md` — 教练对话提炼后的素材（不是逐字稿）
- `reports/` — 反思和月度体检报告
- `profile/` — 画像（详见各文件顶部说明）

## 隐私

- 本目录全部内容仅供本人和 second-brain skill 自己使用
- 其他 Claude Code 工作会话默认读不到本目录（v1 没有外溢机制）
- 如果迁移或备份，把整个目录一起带走即可——数据是裸 markdown，可读、可改、可版本控制

## 怎么用

### 日常段（白天，秘书模式）

- `开工` 列今日任务清单（工作 / 学习 / 生活三类）
- `完成了 xxx` / `搞定了 xxx` 给清单条目打勾
- `收工` / `下班` 拉清单 + 三段式复盘，末尾询问是否反思

### 反思段（按需，教练模式）

- `+chat` / `开始反思` 开始一段教练式对话
- `+checkup` 月度回顾（融合跨时间观察 + patterns 维护）
```
