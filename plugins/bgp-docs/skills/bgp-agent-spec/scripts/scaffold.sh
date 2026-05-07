#!/usr/bin/env bash
# bgp-agent-spec scaffold: 把 templates/ 拷贝到目标项目。
# usage: scaffold.sh [目标目录]
# 默认目标目录：当前工作目录

set -eu
CLAUDE_SKIPPED=0
CONVENTIONS_SKIPPED=0
CONSTITUTION_SKIPPED=0

TARGET="${1:-.}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"

if [[ -f "$TARGET/AGENTS.md" ]]; then
  echo "✗ $TARGET/AGENTS.md 已存在。请先备份/迁出旧文件后再重试。" >&2
  exit 1
fi

mkdir -p "$TARGET/docs/agents"
cp "$TEMPLATES/AGENTS.md" "$TARGET/AGENTS.md"
if [[ -f "$TARGET/CLAUDE.md" ]]; then
  echo "⚠ $TARGET/CLAUDE.md 已存在，未覆盖。请手动添加一行 \`@AGENTS.md\` 到现有 CLAUDE.md。"
  CLAUDE_SKIPPED=1
else
  cp "$TEMPLATES/CLAUDE.md" "$TARGET/CLAUDE.md"
  CLAUDE_SKIPPED=0
fi
if [[ -f "$TARGET/docs/agents/meta-conventions.md" ]]; then
  echo "⚠ $TARGET/docs/agents/meta-conventions.md 已存在，未覆盖。如需更新，请先备份旧文件再重试。"
  CONVENTIONS_SKIPPED=1
else
  cp "$TEMPLATES/docs/agents/meta-conventions.md" "$TARGET/docs/agents/meta-conventions.md"
  CONVENTIONS_SKIPPED=0
fi
if [[ -f "$TARGET/docs/agents/constitution.md" ]]; then
  echo "⚠ $TARGET/docs/agents/constitution.md 已存在，未覆盖。如需更新，请先备份旧文件再重试。"
  CONSTITUTION_SKIPPED=1
else
  cp "$TEMPLATES/docs/agents/constitution.md" "$TARGET/docs/agents/constitution.md"
  CONSTITUTION_SKIPPED=0
fi

echo
echo "✓ 已写入："
echo "  - $TARGET/AGENTS.md"
if [[ "$CONSTITUTION_SKIPPED" -eq 0 ]]; then
  echo "  - $TARGET/docs/agents/constitution.md"
else
  echo "  - docs/agents/constitution.md（已存在，未覆盖）"
fi
if [[ "$CONVENTIONS_SKIPPED" -eq 0 ]]; then
  echo "  - $TARGET/docs/agents/meta-conventions.md"
else
  echo "  - docs/agents/meta-conventions.md（已存在，未覆盖）"
fi
if [[ "$CLAUDE_SKIPPED" -eq 0 ]]; then
  echo "  - $TARGET/CLAUDE.md"
else
  echo "  - CLAUDE.md（已存在，未覆盖）"
fi
echo
echo "下一步："
echo "  1. 编辑 AGENTS.md 填空（命令、命名、单例实现等占位 <...>）"
echo "  2. 需要新增模块规范时，照搬 docs/agents/meta-conventions.md 末尾的「模块规范文件最小骨架」"
