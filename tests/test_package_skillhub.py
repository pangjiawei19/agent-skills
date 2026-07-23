from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_skillhub import PackageError, build_package, slugify_name


VALID_DESCRIPTION = (
    "当用户需要准备或修改演讲、分享或培训，并需要组织大纲、讲稿或演示材料时使用。"
)


class PackageSkillHubTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_skill(
        self,
        *,
        name: str = "preparing-presentations",
        version: str | None = "1.0.0",
    ) -> Path:
        skill_dir = self.root / "preparing-presentations"
        skill_dir.mkdir()
        frontmatter = [
            "---",
            f"name: {name}",
            f'description: "{VALID_DESCRIPTION}"',
        ]
        if version is not None:
            frontmatter.append(f"version: {version}")
        frontmatter.extend(["---", "", "# Preparing Presentations", ""])
        (skill_dir / "SKILL.md").write_text("\n".join(frontmatter), encoding="utf-8")
        references = skill_dir / "references"
        references.mkdir()
        (references / "guide.md").write_text("# Guide\n", encoding="utf-8")
        return skill_dir

    def test_slugifies_name_using_skillhub_rules(self) -> None:
        self.assertEqual(slugify_name("Preparing Presentations"), "preparing-presentations")
        self.assertEqual(slugify_name("AI 演讲助手"), "ai-演讲助手")

    def test_builds_zip_with_one_top_level_directory(self) -> None:
        skill_dir = self.create_skill()
        output_dir = self.root / "dist"

        archive = build_package(skill_dir, "preparing-presentations", output_dir)

        self.assertEqual(archive.name, "preparing-presentations-1.0.0.zip")
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(
                sorted(bundle.namelist()),
                [
                    "preparing-presentations/SKILL.md",
                    "preparing-presentations/references/guide.md",
                ],
            )

    def test_rejects_missing_version(self) -> None:
        skill_dir = self.create_skill(version=None)

        with self.assertRaisesRegex(PackageError, "version"):
            build_package(skill_dir, "preparing-presentations", self.root / "dist")

    def test_rejects_slug_mismatch(self) -> None:
        skill_dir = self.create_skill()

        with self.assertRaisesRegex(PackageError, "slug"):
            build_package(skill_dir, "different-slug", self.root / "dist")

    def test_rejects_slug_shorter_than_two_characters(self) -> None:
        skill_dir = self.create_skill(name="a")

        with self.assertRaisesRegex(PackageError, "2-64"):
            build_package(skill_dir, "a", self.root / "dist")

    def test_rejects_disallowed_extension(self) -> None:
        skill_dir = self.create_skill()
        (skill_dir / "payload.exe").write_bytes(b"MZ")

        with self.assertRaisesRegex(PackageError, "extension"):
            build_package(skill_dir, "preparing-presentations", self.root / "dist")

    def test_rejects_content_that_does_not_match_extension(self) -> None:
        skill_dir = self.create_skill()
        (skill_dir / "fake.png").write_text("not a png", encoding="utf-8")

        with self.assertRaisesRegex(PackageError, "content"):
            build_package(skill_dir, "preparing-presentations", self.root / "dist")

    def test_rejects_symbolic_links(self) -> None:
        skill_dir = self.create_skill()
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        link = skill_dir / "linked.md"
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest(f"symbolic links unavailable: {error}")

        with self.assertRaisesRegex(PackageError, "symbolic link"):
            build_package(skill_dir, "preparing-presentations", self.root / "dist")


if __name__ == "__main__":
    unittest.main()
