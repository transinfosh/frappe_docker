import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / "resources/release/prepare_release.py"
SPEC = importlib.util.spec_from_file_location("prepare_release", SCRIPT)
prepare_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(prepare_release)


class PrepareReleaseTest(unittest.TestCase):
    def test_build_apps_json_does_not_include_lock_metadata(self):
        extra_apps = [
            {
                "url": "https://github.com/transinfosh/base.git",
                "branch": "develop",
                "commit": "a" * 40,
            }
        ]

        self.assertEqual(
            prepare_release.build_apps_json(
                "transinfosh/quality", "v1.2.3", extra_apps
            ),
            [
                {
                    "url": "https://github.com/transinfosh/quality.git",
                    "branch": "v1.2.3",
                },
                {"url": "https://github.com/transinfosh/base.git", "branch": "develop"},
            ],
        )

    def test_load_extra_apps_requires_immutable_commit(self):
        with self.assertRaisesRegex(ValueError, "40 位 commit"):
            prepare_release.load_extra_apps(
                '[{"url":"https://github.com/transinfosh/base.git","branch":"develop"}]'
            )

    def test_validate_tag_requires_version_match(self):
        with self.assertRaisesRegex(ValueError, "不一致"):
            prepare_release.validate_tag("v1.2.4", "1.2.3")

    @patch.object(prepare_release.subprocess, "run")
    def test_validate_dependency_locks_rejects_moved_branch(self, run):
        run.return_value.stdout = f"{'b' * 40}\trefs/heads/develop\n"
        apps = [
            {
                "url": "https://github.com/transinfosh/base.git",
                "branch": "develop",
                "commit": "a" * 40,
            }
        ]

        with self.assertRaisesRegex(ValueError, "锁定提交"):
            prepare_release.validate_dependency_locks(apps)

    @patch.object(prepare_release.subprocess, "run")
    def test_validate_dependency_locks_accepts_a_tag(self, run):
        commit = "a" * 40
        run.return_value.stdout = f"{commit}\trefs/tags/v1.2.3\n"
        apps = [
            {
                "url": "https://github.com/transinfosh/base.git",
                "branch": "v1.2.3",
                "commit": commit,
            }
        ]

        prepare_release.validate_dependency_locks(apps)

        self.assertIn("refs/tags/v1.2.3", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
