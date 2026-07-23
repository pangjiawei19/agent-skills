# SkillHub 发布适配设计

> 状态：已确认，待实现。

## 目标

让 `preparing-presentations` 满足 SkillHub ZIP 上传规范，并建立可重复的仓库级校验与打包流程。

## 元数据调整

`skills/preparing-presentations/SKILL.md` frontmatter 调整为：

```yaml
---
name: preparing-presentations
description: "当用户需要准备或修改演讲、经验分享、技术分享、培训课程或主题演示，尤其是主题模糊、素材零散、叙事结构不清，或需要大纲、讲稿、故事板、排练计划与演示文件时使用。"
version: 1.0.0
---
```

- `name` 保持不变，生成的 slug 仍为 `preparing-presentations`。
- `description` 使用中文并只描述触发场景，不概述内部流程。
- 首次发布版本使用 `1.0.0`；若 SkillHub 已存在同 slug，发布前改为严格大于最大版本的版本号。

Codex `quick_validate.py` 当前不允许顶层 `version`，与 SkillHub 强制版本号存在兼容冲突。发布校验以本设计的 SkillHub 校验器为准；行为验证继续使用既有 RED／GREEN 评估。

## 发布脚本

新增 `scripts/package_skillhub.py`，命令：

```bash
uv run --with pyyaml python scripts/package_skillhub.py \
  skills/preparing-presentations \
  --slug preparing-presentations \
  --output-dir dist/skillhub
```

脚本负责：

1. 读取并验证 YAML frontmatter；
2. 检查 `name`、单行 `description`、`x.y.z` 版本；
3. 按 SkillHub 规则从 name 生成 slug，并与 `--slug` 对比；
4. 检查保留字、2～64 字符及连字符规则；
5. 拒绝符号链接、绝对路径和路径穿越；
6. 检查文件数量、单文件大小、总大小和允许扩展名；
7. 对文本、PDF、图片和 Office 文件做基础内容签名检查；
8. 生成只包含技能目录的 `<slug>-<version>.zip`；
9. 重新读取 ZIP，确认只有一个顶层目录，且剥除后根目录存在 `SKILL.md`。

限制采用：最多 100 个文件、单文件最多 10 MB、解压总大小最多 100 MB、ZIP 最多 100 MB。单文件使用文档中更严格的 10 MB，避免服务端错误表所述限制。

## 测试

新增 `tests/test_package_skillhub.py`，使用 `unittest` 和临时目录覆盖：

- 当前 frontmatter 缺少 version 时失败；
- 合法技能可以生成正确命名的 ZIP；
- name 生成的 slug 与传入 slug 不一致时失败；
- 非法扩展名失败；
- 符号链接失败；
- ZIP 只有一个顶层技能目录，且包含根 `SKILL.md`。

## 仓库与产物

- `dist/` 加入 `.gitignore`。
- 脚本与测试进入 Git。
- 生成的 ZIP 只作为本地发布产物，不提交 Git。
- 不把设计、测试或打包脚本放进技能 ZIP。

## 完成标准

1. 所有单元测试通过；
2. 当前 Skill 通过 SkillHub 校验器；
3. 生成 `dist/skillhub/preparing-presentations-1.0.0.zip`；
4. ZIP 解包后只有一个顶层目录，剥除后根目录存在 `SKILL.md`；
5. ZIP 中只有当前 Skill 的 5 个文件；
6. Git 工作树只包含应提交的源文件，不跟踪 ZIP。
