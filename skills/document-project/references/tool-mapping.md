# 工具映射表（跨 Agent 平台）

本 skill 的主文件使用 Claude Code 的工具名称。如果你在其他 Agent 平台运行，请参考下表替换为等价能力。

## 核心能力映射

| 能力 | Claude Code | Copilot CLI | Codex | Gemini CLI | 通用 Agent SDK |
|------|-------------|-------------|-------|------------|----------------|
| 按文件名/路径模式查找 | `Glob` | `file_search` | `FindFiles` | `glob` | 文件系统 glob 调用 |
| 按内容正则搜索 | `Grep` | `grep` | `Grep` | `search_file_content` | ripgrep / grep 封装 |
| 读取文件 | `Read` | `read` | `Read` | `read_file` | fs.readFile |
| 执行 shell 命令 | `Bash` | `bash` | `Shell` | `run_shell_command` | child_process |
| 写入文件 | `Write` | `write` | `Write` | `write_file` | fs.writeFile |
| 编辑文件 | `Edit` | `edit` | `Edit` | `replace` | 差异补丁 |
| 派发子任务（并行分析） | `Agent`（subagent_type=Explore） | subagent | Task | `dispatch_agent` | 子 agent 调用 |

## 语义级探索

Claude Code 没有独立的"语义搜索"工具。需要开放式探索（如 "Where are entity classes?"）时，用 `Agent` + `subagent_type=Explore` 派发子 agent，让它通过 Grep/Glob/Read 组合完成。其他平台若有内置向量检索则直接使用；否则同样"关键字搜索 + 读取 + 推断"。

## 使用原则

- 主文件中若出现具体工具名（如 `Grep`、`Glob`），优先理解为**该操作的意图**（搜索、查找、读取），再选择你所在平台的对应工具。
- 如果平台没有并行子 agent 能力，顺序执行即可，但需要注意控制 context 占用。
- Shell 命令（`git log`、`git diff`）在所有主流平台都能通过 bash/shell 工具执行，无需替换。
