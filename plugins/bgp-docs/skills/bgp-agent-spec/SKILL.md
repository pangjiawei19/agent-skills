---
name: bgp-agent-spec
description: 在新项目中安装一套 AI agent 执行的规范骨架。当用户提到："给项目加规范 / 安装 AGENTS.md / scaffold agents spec / 让 Claude 知道项目约定" 时调用。scaffold 后项目自包含，不再依赖本 skill。
---

# bgp-agent-spec scaffold

## 何时使用

用户在一个**新项目**里希望落下一套"AI agent 工作约定"骨架时调用。

## 执行步骤

1. 确认目标目录（默认当前工作目录），用户若指定路径则用指定路径
2. 调用 `scripts/scaffold.sh <目标目录>`
3. 若脚本因 `AGENTS.md` 已存在而中止：向用户复述脚本输出，不要自行覆盖、不要"智能合并"。让用户决定是改名旧文件还是放弃 scaffold
4. scaffold 成功后，转述脚本输出即可，不要额外解释模板内容

## 不要做

- 不要绕过 `scaffold.sh` 直接用 Edit/Write 创建模板文件
- 不要替用户填占位符（命令、命名风格等）——这些是项目决策，让用户自己想
- 不要在 scaffold 后解释 `meta-conventions.md` 的内容——它已经写得足够清楚，让用户自己读
