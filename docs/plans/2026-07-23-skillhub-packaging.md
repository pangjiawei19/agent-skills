# SkillHub Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `preparing-presentations` 增加 SkillHub 元数据、发布校验和可重复 ZIP 打包能力。

**Architecture:** 使用一个依赖 PyYAML 的 Python CLI 完成验证与打包，测试使用标准库 `unittest` 和临时目录。发布产物写入被 Git 忽略的 `dist/skillhub/`，技能包本身仍只包含原有 5 个文件。

**Tech Stack:** Python 3、PyYAML、unittest、zipfile、Git。

## Global Constraints

- 首次发布版本为 `1.0.0`。
- slug 固定为 `preparing-presentations`。
- ZIP 只包含 `skills/preparing-presentations/` 下的文件。
- 单文件上限采用 10 MB，总文件数 100，总解压大小 100 MB，ZIP 大小 100 MB。
- 不提交生成的 ZIP。
- 修改脚本必须遵循 RED－GREEN－REFACTOR。

### Task 1: 写失败测试

**Files:**
- Create: `tests/test_package_skillhub.py`
- Modify: `.gitignore`

- [ ] 创建使用临时目录的 unittest，覆盖合法打包、缺少 version、slug 不匹配、非法扩展、符号链接和 ZIP 结构。
- [ ] 运行 `uv run --with pyyaml python -m unittest tests/test_package_skillhub.py -v`。
- [ ] 预期因 `scripts.package_skillhub` 不存在而失败，确认 RED 原因正确。

### Task 2: 实现最小校验与打包器

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/package_skillhub.py`

- [ ] 实现 `PackageError`、`slugify_name()`、`read_metadata()`、`collect_files()`、`validate_content_type()`、`build_package()`。
- [ ] CLI 接受 `skill_dir`、`--slug`、`--output-dir`，成功时输出 ZIP 路径和校验摘要，失败时退出码为 1。
- [ ] 运行全部测试，预期 PASS。

### Task 3: 更新 SkillHub 元数据并生成真实包

**Files:**
- Modify: `skills/preparing-presentations/SKILL.md`

- [ ] 将 description 改为设计中的中文触发描述并增加 `version: 1.0.0`。
- [ ] 运行单元测试。
- [ ] 执行真实打包命令生成 `dist/skillhub/preparing-presentations-1.0.0.zip`。
- [ ] 使用 `unzip -l` 检查 ZIP 恰好包含 5 个文件，并且只有一个顶层目录。

### Task 4: 最终验证与提交

- [ ] 运行 `git diff --check`。
- [ ] 确认 `git status --short` 不包含 `dist/`。
- [ ] 运行全部单元测试和一次真实打包。
- [ ] 提交元数据、脚本、测试、设计与计划，commit message：`feat: add SkillHub packaging`。

## Self-Review

- 设计的元数据、slug、文件限制、安全路径、扩展名、内容签名和 ZIP 根结构均有实现任务。
- 每个脚本行为均由测试先定义。
- 发布 ZIP 被明确排除在 Git 提交之外。
