---
name: second-brain
description: 个人第二大脑：通过教练式对话、按需深度反思、月度体检，沉淀关于"我、agent 自己、协作模式"的画像并引发思考。Shortcuts：+chat（开启教练式对话）、+reflect（按需深度反思报告）、+checkup（月度体检报告）。用户提及"第二大脑"、"复盘一下"、"反思一下"、"我想倒一倒"、"聊聊我自己"、"月度体检"时触发。
---

# Second Brain

这是一个个人"第二大脑"——通过持续对话沉淀画像、引发思考。

**CRITICAL — 任何 Shortcut 执行前 MUST 先用 Read 工具完整读取其对应的 reference 文件，禁止凭印象执行！**

**CRITICAL — 首次运行检查：** 每次 skill 被调用时，先检查 `~/second-brain/` 是否存在。如不存在，MUST 先用 Read 工具读取 [`references/init.md`](references/init.md) 并按其执行初始化，再继续当前 shortcut。

**CRITICAL — 隐私边界（硬约定）：**
- `~/second-brain/raw/` 和 `~/second-brain/reports/` 仅供本 skill 自己读取
- `~/second-brain/profile/` 也仅供本 skill 自己读取（v1 不外溢到其他工作会话）
- 任何情况下，禁止将上述目录的内容主动展示或转贴到其他工具/对话语境，除非用户显式要求

## 数据目录

```
~/second-brain/
├── raw/                      # 提炼后的对话素材（按月分文件，YYYY-MM.md）
├── reports/                  # 报告（反思 + 体检）
├── profile/
│   ├── user.md               # 关于"我"：身份、价值观、长期目标、重要的人
│   ├── soul.md               # 关于 agent：性格、说话风格、忌讳、与用户的边界
│   ├── patterns.md           # 观察到的规律（含显式偏好和归纳出的人格规律）
│   └── memory.md             # 最近的状态、在忙/烦的事
└── README.md
```

## Shortcuts

| Shortcut | 用途 | Reference |
|---|---|---|
| `+chat` | 开始一段教练式对话，结束时自动提炼到 raw/、按需更新 profile/ | [`references/chat.md`](references/chat.md) |
| `+reflect [--window <span>]` | 按需深度反思报告（默认窗口最近 2 周） | [`references/reflect.md`](references/reflect.md) |
| `+checkup [--month YYYY-MM]` | 月度体检报告 + 提议 patterns 更新（不带参数 = 上个月） | [`references/checkup.md`](references/checkup.md) |

## 全局行为约束（适用所有 shortcut）

1. **加载 profile**：每个 shortcut 开始时，用 Read 工具读取 `~/second-brain/profile/` 下全部 4 个文件，作为对话上下文。即使是 `+reflect` / `+checkup` 这类不"对话"的命令，也要加载 profile（特别是 `soul.md` 决定 agent 人格）。
2. **不要泄密**：raw/ 和 reports/ 仅在 shortcut 内部使用，不出现在跨会话/跨工具输出中。
3. **遵循 soul.md**：用户在 `soul.md` 里定义的 agent 人格优先于本 skill 默认风格。
4. **遵循 patterns.md**：用户在 `patterns.md` 里定义的显式偏好（如"别一次问多个问题"）必须遵守。

## 文件写入分级（CRITICAL）

| 文件 | 写入方式 |
|---|---|
| `raw/YYYY-MM.md` | 自动追加，不审阅 |
| `reports/*.md` | 自动写，不审阅 |
| `profile/memory.md` | 自动重写（仅反映"现在"，不留历史） |
| `profile/patterns.md` | **提议后写**（必须用户口头确认才写） |
| `profile/user.md` | **提议后写**（必须用户口头确认才写） |
| `profile/soul.md` | **提议后写**（必须用户口头确认才写） |

绝不擅自改 patterns/user/soul 三者。
