# 自进化机制加装指南

用于把自进化闭环安装到某个目标 Skill。安装前必须先读目标 `SKILL.md`，必要时再读目标 references。

## １．识别目标

确认：

- Skill 名称；
- Skill 根目录；
- Skill 是项目内还是全局；
- 是否已有 `version` 字段，或用户是否要求启用版本管理；
- 目标 Skill 的主流程；
- 目标 Skill 的主要产物；
- 目标 Skill 的高风险动作。

如果目标 Skill 有多个流程，只先覆盖用户当前要求的流程，不一次性改完整个 Skill。

## ２．选择数据目录

项目 Skill：

```text
<project-root>/skill-self-evolution/skill-runs/<skill-name>/
<project-root>/skill-self-evolution/skill-reviews/<skill-name>/
```

全局 Skill：

```text
~/.agents/skill-self-evolution/skill-runs/<skill-name>/
~/.agents/skill-self-evolution/skill-reviews/<skill-name>/
```

如果用户指定其他路径，使用用户路径，并在方案中写明。

## ３．提出加装方案

在修改前先向用户说明：

- 将创建哪些目录；
- 将修改目标 Skill 的哪些文件；
- 每个流程结束后如何写运行轨迹；
- 何时触发阶段复盘；
- 哪些情况才允许修改目标 Skill；
- 是否维护 `SKILL.md` frontmatter 顶层 `version` 字段，以及本次是否需要初始化版本；
- 回归检查会覆盖哪些路径。

用户确认后再修改。

## ４．修改目标 Skill

常见修改点：

1. 在目标 `SKILL.md` 的目录约定中加入 runs/reviews 目录。
2. 在目标路由中加入“复盘 / 迭代 / 分析运行轨迹”意图。
3. 在目标主流程的收尾步骤后加入“写入运行轨迹”。
4. 在目标 `SKILL.md` 中加入自进化闭环规则：
   - 运行轨迹；
   - 复盘触发；
   - 修改边界；
   - 回归检查。
5. 如果目标 Skill 有模板文件，把运行轨迹、复盘报告和回归检查模板加入模板文件；否则在 references 下新增一个模板文件。
6. 如果用户要求启用版本管理，或目标 Skill 已经存在 `version` 字段，在目标 `SKILL.md` frontmatter 顶层维护 `version`。

## ５．修改边界

必须遵守：

- 单次运行问题先记录，默认不改 Skill。
- 同类问题出现 ２ 次以上，或出现高风险问题，才建议进入复盘。
- 单次复盘最多让 １～３ 条建议进入本轮修改。
- 修改前说明证据、改动位置、预期收益、潜在风险。
- 用户确认后再改。
- 如果本轮修改改变了规则、流程、模板或保护边界，并且目标 Skill 启用了版本管理，同步更新顶层 `version`。
- 修改后执行回归检查。

## ６．验收

加装完成后验证：

- runs/reviews 目录存在；
- 目标 Skill 能说明何时写运行轨迹；
- 目标 Skill 能说明何时做阶段复盘；
- 目标 Skill 没有绕过用户确认自动修改自身；
- 如果启用了版本管理，`SKILL.md` frontmatter 顶层存在 `version`，且版本号与本轮改动性质匹配；
- 回归检查清单覆盖目标 Skill 的主路径和高风险动作。
