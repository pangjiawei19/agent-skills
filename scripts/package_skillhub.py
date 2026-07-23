#!/usr/bin/env python3
"""校验并打包符合 SkillHub 上传要求的 Skill。"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

import yaml


MAX_FILE_COUNT = 100
MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 100 * 1024 * 1024
MAX_ARCHIVE_SIZE = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".xsd",
    ".xsl",
    ".dtd",
    ".ini",
    ".cfg",
    ".env",
    ".html",
    ".css",
    ".csv",
    ".pdf",
    ".js",
    ".cjs",
    ".mjs",
    ".ts",
    ".py",
    ".sh",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".lua",
    ".sql",
    ".r",
    ".bat",
    ".ps1",
    ".zsh",
    ".bash",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".gif",
    ".webp",
    ".ico",
    ".doc",
    ".xls",
    ".ppt",
    ".docx",
    ".xlsx",
    ".pptx",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".xsd",
    ".xsl",
    ".dtd",
    ".ini",
    ".cfg",
    ".env",
    ".html",
    ".css",
    ".csv",
    ".js",
    ".cjs",
    ".mjs",
    ".ts",
    ".py",
    ".sh",
    ".rb",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".lua",
    ".sql",
    ".r",
    ".bat",
    ".ps1",
    ".zsh",
    ".bash",
    ".svg",
}

RESERVED_SLUGS = {
    "admin",
    "api",
    "dashboard",
    "search",
    "auth",
    "me",
    "global",
    "system",
    "static",
    "assets",
    "health",
}

FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
SLUG_PATTERN = re.compile(r"^[a-z0-9\u0080-\uffff](?:[a-z0-9\u0080-\uffff-]{0,62}[a-z0-9\u0080-\uffff])?$")


class PackageError(ValueError):
    """SkillHub 校验或打包失败。"""


def slugify_name(name: str) -> str:
    """按 SkillHub 规则将名称转换为 slug。"""

    normalized: list[str] = []
    previous_was_separator = False
    for char in name.strip().lower():
        if char.isalnum() or char == "-":
            if char == "-":
                if previous_was_separator:
                    continue
                previous_was_separator = True
            else:
                previous_was_separator = False
            normalized.append(char)
        elif not previous_was_separator:
            normalized.append("-")
            previous_was_separator = True
    return "".join(normalized).strip("-")


def read_metadata(skill_dir: Path) -> dict[str, str]:
    """读取并校验 SKILL.md frontmatter。"""

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise PackageError("skill root must contain SKILL.md")

    try:
        text = skill_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PackageError("SKILL.md content must be valid UTF-8") from exc

    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise PackageError("SKILL.md must start with YAML frontmatter")

    try:
        raw_metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise PackageError(f"invalid SKILL.md frontmatter: {exc}") from exc

    if not isinstance(raw_metadata, dict):
        raise PackageError("SKILL.md frontmatter must be a mapping")

    metadata: dict[str, str] = {}
    for field in ("name", "description", "version"):
        value = raw_metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PackageError(f"frontmatter field '{field}' must be a non-empty string")
        metadata[field] = value.strip()

    if "\n" in metadata["description"] or "\r" in metadata["description"]:
        raise PackageError("description must be a single line")
    if not VERSION_PATTERN.fullmatch(metadata["version"]):
        raise PackageError("version must use x.y.z format")

    return metadata


def _extension(path: Path) -> str:
    if path.name.lower() == ".env":
        return ".env"
    return path.suffix.lower()


def collect_files(skill_dir: Path) -> list[Path]:
    """收集并校验待打包文件。"""

    if not skill_dir.is_dir():
        raise PackageError(f"skill directory does not exist: {skill_dir}")

    files: list[Path] = []
    total_size = 0
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise PackageError(f"symbolic link is not allowed: {path.relative_to(skill_dir)}")
        if not path.is_file():
            continue

        relative_path = path.relative_to(skill_dir)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise PackageError(f"unsafe relative path: {relative_path}")

        extension = _extension(path)
        if extension not in ALLOWED_EXTENSIONS:
            raise PackageError(f"file extension is not allowed: {relative_path}")

        size = path.stat().st_size
        if size > MAX_SINGLE_FILE_SIZE:
            raise PackageError(f"file exceeds 10 MB limit: {relative_path}")
        total_size += size
        files.append(path)

    if not files:
        raise PackageError("skill directory contains no files")
    if len(files) > MAX_FILE_COUNT:
        raise PackageError(f"file count exceeds {MAX_FILE_COUNT}")
    if total_size > MAX_TOTAL_SIZE:
        raise PackageError("uncompressed content exceeds 100 MB limit")

    return files


def _has_signature(data: bytes, signature: bytes) -> bool:
    return data.startswith(signature)


def validate_content_type(path: Path) -> None:
    """用轻量魔数或 UTF-8 校验阻止伪造扩展名。"""

    extension = _extension(path)
    data = path.read_bytes()

    if extension in TEXT_EXTENSIONS:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PackageError(f"content does not match UTF-8 text extension: {path.name}") from exc
        return

    valid = True
    if extension == ".png":
        valid = _has_signature(data, b"\x89PNG\r\n\x1a\n")
    elif extension in {".jpg", ".jpeg"}:
        valid = _has_signature(data, b"\xff\xd8\xff")
    elif extension == ".gif":
        valid = data.startswith((b"GIF87a", b"GIF89a"))
    elif extension == ".webp":
        valid = len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    elif extension == ".ico":
        valid = _has_signature(data, b"\x00\x00\x01\x00")
    elif extension == ".pdf":
        valid = _has_signature(data, b"%PDF-")
    elif extension in {".doc", ".xls", ".ppt"}:
        valid = _has_signature(data, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    elif extension in {".docx", ".xlsx", ".pptx"}:
        expected_prefix = {".docx": "word/", ".xlsx": "xl/", ".pptx": "ppt/"}[extension]
        try:
            with zipfile.ZipFile(path) as office_archive:
                names = office_archive.namelist()
                valid = "[Content_Types].xml" in names and any(
                    name.startswith(expected_prefix) for name in names
                )
        except zipfile.BadZipFile:
            valid = False

    if not valid:
        raise PackageError(f"content does not match file extension: {path.name}")


def _validate_slug(slug: str) -> None:
    if not 2 <= len(slug) <= 64 or not SLUG_PATTERN.fullmatch(slug):
        raise PackageError("slug must be 2-64 lowercase characters with single internal hyphens")
    if "--" in slug:
        raise PackageError("slug must not contain consecutive hyphens")
    if slug in RESERVED_SLUGS:
        raise PackageError(f"slug is reserved: {slug}")


def build_package(skill_dir: Path, slug: str, output_dir: Path) -> Path:
    """校验 Skill 并生成包含单一顶层目录的 ZIP。"""

    skill_dir = skill_dir.resolve()
    metadata = read_metadata(skill_dir)
    expected_slug = slugify_name(metadata["name"])
    if expected_slug != slug:
        raise PackageError(f"slug mismatch: expected '{expected_slug}', got '{slug}'")
    _validate_slug(slug)

    files = collect_files(skill_dir)
    for path in files:
        validate_content_type(path)

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{slug}-{metadata['version']}.zip"

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative_path = path.relative_to(skill_dir)
            archive.write(path, Path(slug) / relative_path)

    if archive_path.stat().st_size > MAX_ARCHIVE_SIZE:
        archive_path.unlink(missing_ok=True)
        raise PackageError("ZIP archive exceeds 100 MB limit")

    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            top_levels = {Path(name).parts[0] for name in members}
            if top_levels != {slug}:
                raise PackageError("ZIP must contain exactly one top-level skill directory")
            if f"{slug}/SKILL.md" not in members:
                raise PackageError("ZIP does not contain the root SKILL.md")
            if len(members) != len(files):
                raise PackageError("ZIP file count differs from validated source")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise PackageError(f"ZIP integrity check failed: {bad_member}")
    except zipfile.BadZipFile as exc:
        raise PackageError("generated ZIP is invalid") from exc

    return archive_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path, help="待打包 Skill 目录")
    parser.add_argument("--slug", required=True, help="SkillHub slug")
    parser.add_argument("--output-dir", type=Path, default=Path("dist/skillhub"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        archive_path = build_package(args.skill_dir, args.slug, args.output_dir)
    except PackageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"SkillHub package created: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
