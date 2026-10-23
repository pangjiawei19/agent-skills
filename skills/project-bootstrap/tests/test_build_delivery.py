"""构建交付资源的离线回归；仅使用临时目录和 Docker、AWS、通知替身。"""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import patch


ASSETS = Path(__file__).resolve().parents[1] / "assets" / "build-delivery"
SHA = "a" * 40
DIGEST = "sha256:" + "b" * 64
REGISTRY = "123456789012.dkr.ecr.us-east-1.amazonaws.com"
IMAGE_ID = "sha256:" + "c" * 64
SPECS = {name: {"repository": f"synthetic/{name}", "target": "runtime", "platform": "linux/amd64"}
         for name in ("app", "worker")}


def image_record(component="app", job_id="1"):
    tag = f"release-{component}-{job_id}-{SHA[:8]}"
    return {"schema_version": 2, "component": component, "target": "runtime", "platform": "linux/amd64",
            "commit_sha": SHA, "pipeline_id": "42", "job_id": job_id, "built_at": "2026-10-20T00:00:00+00:00",
            "image_uri": f"{REGISTRY}/synthetic/{component}:{tag}", "tag": tag, "digest": DIGEST,
            "image_id": IMAGE_ID, "push_state": "confirmed", "status": "pushed", "stage": "complete", "exit_code": 0}


spec = importlib.util.spec_from_file_location("bootstrap_notice", ASSETS / "notify-feishu.py")
notice = importlib.util.module_from_spec(spec)
with patch.object(sys, "path", [str(ASSETS), *sys.path]):
    spec.loader.exec_module(notice)


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bootstrap-notice-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.previous_directory = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous_directory)
        self.environment = patch.dict(os.environ, {
            "CI_COMMIT_SHA": SHA,
            "CI_PIPELINE_ID": "42",
            "CI_PIPELINE_URL": "https://gitlab.example.test/group/project/-/pipelines/42",
            "CI_PROJECT_URL": "https://gitlab.example.test/group/project", "CI_PROJECT_PATH": "group/project",
            "CI_COMMIT_REF_NAME": "release/test",
            "EXPECTED_IMAGE_SPECS": json.dumps(SPECS), "ECR_REGISTRY": REGISTRY,
        }, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        (self.root / "build-results").mkdir()
        (self.root / "verify-exit-code.txt").write_text("0\n")
        (self.root / "source-scan-exit-code.txt").write_text("0\n")
        self.good_path = self.root / "build-results/app-1.json"
        self.good_record = image_record()
        self.good_path.write_text(json.dumps(self.good_record))
        self.bad_path = self.root / "build-results/worker-2.json"

    def run_notice(self, outcome="failure", collect_only=False):
        arguments = ["notify-feishu.py", "--outcome", outcome]
        if collect_only:
            arguments.append("--collect-only")
        with patch.object(sys, "argv", arguments), patch.object(notice, "send_notice") as sender:
            notice.main()
        return sender

    def result(self):
        return json.loads((self.root / "build-result.json").read_text())

    def assert_failure_summary(self, sender):
        sender.assert_called_once()
        result = self.result()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["images"], [self.good_record])
        self.assertTrue(result["collection_errors"])
        text = sender.call_args.args[0]["content"]["text"]
        self.assertIn("https://gitlab.example.test/group/project/-/pipelines/42", text)
        self.assertIn(DIGEST, text)
        self.assertIn("校验", text)
        self.assertNotIn("synthetic-confidential", json.dumps(result) + text)
        self.assertEqual(json.loads(self.good_path.read_text()), self.good_record)

    def test_failure_notice_keeps_valid_component_when_json_is_corrupt(self):
        self.bad_path.write_text("{synthetic-confidential")
        self.assert_failure_summary(self.run_notice())

    def test_success_rejects_corrupt_record_without_sending(self):
        self.bad_path.write_text("{synthetic-confidential")
        with patch.object(sys, "argv", ["notify-feishu.py", "--outcome", "success"]), \
                patch.object(notice, "send_notice") as sender:
            with self.assertRaises(ValueError):
                notice.main()
            sender.assert_not_called()

    def test_failure_notice_rejects_other_pipeline_record(self):
        self.bad_path.write_text(json.dumps({**self.good_record, "component": "worker", "pipeline_id": "41"}))
        self.assert_failure_summary(self.run_notice())

    def test_failure_notice_skips_invalid_record_shapes(self):
        for value in [None, [], {}, {**self.good_record, "component": None},
                      {**self.good_record, "digest": {"secret": "synthetic-confidential"}}]:
            with self.subTest(value=value):
                self.bad_path.write_text(json.dumps(value))
                self.assert_failure_summary(self.run_notice())

    def test_failure_notice_survives_record_read_error(self):
        self.bad_path.write_text("{}")
        original = Path.read_text

        def read(path, *args, **kwargs):
            if path == self.bad_path or path == Path("build-results/worker-2.json"):
                raise PermissionError("synthetic-confidential")
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", read):
            self.assert_failure_summary(self.run_notice())

    def test_failure_notice_survives_invalid_components_and_verification(self):
        for field in ["components", "verification"]:
            with self.subTest(field=field):
                with patch.dict(os.environ, {"EXPECTED_IMAGE_SPECS": json.dumps(SPECS)}):
                    (self.root / "verify-exit-code.txt").write_text("0\n")
                    if field == "components":
                        os.environ["EXPECTED_IMAGE_SPECS"] = "synthetic-confidential"
                    else:
                        (self.root / "verify-exit-code.txt").write_text("synthetic-confidential")
                    self.assert_failure_summary(self.run_notice())

    def test_complete_components_can_succeed(self):
        self.bad_path.write_text(json.dumps(image_record("worker", "2")))
        sender = self.run_notice("success")
        sender.assert_called_once()
        self.assertEqual(self.result()["status"], "complete")
        self.assertEqual(len(self.result()["images"]), 2)

    def test_missing_component_cannot_succeed(self):
        with self.assertRaises(ValueError):
            self.run_notice("success")
        self.assertEqual(self.result()["status"], "failed")

    def test_collect_only_does_not_send(self):
        self.bad_path.write_text("{synthetic-confidential")
        self.run_notice(collect_only=True).assert_not_called()
        self.assertEqual(self.result()["status"], "failed")

    def test_notification_error_does_not_change_component_result(self):
        self.bad_path.write_text("{synthetic-confidential")
        with patch.object(sys, "argv", ["notify-feishu.py", "--outcome", "failure"]), \
                patch.object(notice, "send_notice", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                notice.main()
        self.assertEqual(self.result()["images"], [self.good_record])
        self.assertEqual(json.loads(self.good_path.read_text()), self.good_record)

    def test_invalid_metadata_is_rejected_even_in_failure_notice(self):
        for update in [
            {"image_uri": "synthetic-confidential\nextra"}, {"tag": "mismatch"},
            {"job_id": "99"}, {"target": "runtime\nsynthetic-confidential"},
            {"platform": "unsupported"}, {"built_at": "invalid-time"},
            {"status": "failed", "stage": "synthetic-confidential", "exit_code": 1},
        ]:
            with self.subTest(update=update):
                self.bad_path.write_text(json.dumps({**image_record("worker", "2"), **update}))
                self.assert_failure_summary(self.run_notice())

    def test_success_does_not_accept_nonempty_but_invalid_metadata(self):
        self.bad_path.write_text(json.dumps({**self.good_record, "component": "worker", "job_id": "2",
                                           "image_uri": "not-an-image", "platform": "unsupported"}))
        with self.assertRaises(ValueError):
            self.run_notice("success")

    def test_manifest_mismatches_and_unknown_fields_never_reach_notice(self):
        for update in [
            {"target": "other"}, {"platform": "linux/arm64"},
            {"image_uri": image_record("worker", "2")["image_uri"].replace("synthetic/worker", "synthetic/other")},
            {"built_at": "2026-02-30T00:00:00Z"}, {"built_at": "2026-10-20T08:00:00+08:00"},
            {"push_state": "unknown"}, {"schema_version": True},
            {"extra": "synthetic-confidential"},
        ]:
            with self.subTest(update=update):
                self.bad_path.write_text(json.dumps({**image_record("worker", "2"), **update}))
                self.assert_failure_summary(self.run_notice())

    def test_polluted_pipeline_context_is_replaced_by_fixed_summary(self):
        self.bad_path.write_text(json.dumps(image_record("worker", "2")))
        for field in ("CI_PIPELINE_URL", "CI_PROJECT_PATH", "CI_COMMIT_REF_NAME", "CI_PROJECT_URL"):
            with self.subTest(field=field), patch.dict(os.environ, {field: "synthetic-confidential\nextra"}):
                sender = self.run_notice()
                result = self.result()
                self.assertEqual(result["status"], "failed")
                self.assertNotIn("synthetic-confidential", json.dumps(result) + str(sender.call_args))
                with self.assertRaises(ValueError):
                    self.run_notice("success")

    def test_source_scan_missing_failed_or_corrupt_blocks_success(self):
        self.bad_path.write_text(json.dumps(image_record("worker", "2")))
        path = self.root / "source-scan-exit-code.txt"
        for value in (None, "19\n", "synthetic-confidential"):
            with self.subTest(value=value):
                path.unlink(missing_ok=True)
                if value is not None:
                    path.write_text(value)
                with self.assertRaises(ValueError):
                    self.run_notice("success")
                sender = self.run_notice()
                self.assertNotIn("synthetic-confidential", str(sender.call_args))

    def test_oversized_and_symlink_records_are_rejected(self):
        self.bad_path.write_text("synthetic-confidential" * 4000)
        self.assert_failure_summary(self.run_notice())
        self.bad_path.unlink()
        self.bad_path.symlink_to(self.good_path)
        self.assert_failure_summary(self.run_notice())

    def test_nested_or_duplicate_json_fields_do_not_break_failure_summary(self):
        for text in ("[" * 2000 + "]" * 2000,
                     json.dumps(image_record("worker", "2")).replace('{', '{"schema_version":2,', 1)):
            with self.subTest(text_size=len(text)):
                self.bad_path.write_text(text)
                self.assert_failure_summary(self.run_notice())

    def test_real_collection_cli_fails_closed_and_never_needs_webhook(self):
        self.bad_path.write_text(json.dumps(image_record("worker", "2")))
        command = [sys.executable, str(ASSETS / "notify-feishu.py"), "--outcome", "success", "--collect-only"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.result()["status"], "complete")
        self.bad_path.write_text("{synthetic-confidential")
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("synthetic-confidential", result.stderr + result.stdout)
        command[command.index("success")] = "failure"
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.result()["images"], [self.good_record])


class BuildPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bootstrap-build-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "scripts/ci").mkdir(parents=True)
        for filename in ("build-record.py", "delivery_contract.py", "run-command.py"):
            shutil.copy(ASSETS / filename, self.root / "scripts/ci" / filename)
        for filename in ("verify-exit-code.txt", "source-scan-exit-code.txt"):
            (self.root / filename).write_text("0\n")
        binary_directory = self.root / "bin"
        binary_directory.mkdir()
        # 替身读取合成登录密码，但不写入调用记录；不会连接 Docker 或 AWS。
        fake_tool = '''#!PYTHON
import json, os, pathlib, signal, subprocess, sys, time
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TEST_CALLS'], 'a') as file:
    file.write(json.dumps([name, *args]) + '\\n')
stage = (args[1] if name == 'aws' else args[0])
stage = {'get-login-password':'ecr_login', 'describe-images':'resolve_digest', 'image':'inspect'}.get(stage, stage)
if os.environ.get('TEST_FAIL_STAGE') == stage:
    sys.exit(27)
if os.environ.get('TEST_HOLD_STAGE') == stage:
    state_path = pathlib.Path(os.environ['TEST_STATE'])
    child_ready = str(state_path) + '.child-ready'
    child_stop = str(state_path) + '.child-stopped'
    child_code = "import pathlib,signal,sys,time; signal.signal(signal.SIGTERM, lambda *_: (pathlib.Path(sys.argv[2]).write_text('stopped'), sys.exit(0))); pathlib.Path(sys.argv[1]).write_text('ready'); time.sleep(60)"
    child = subprocess.Popen([sys.executable, '-c', child_code, child_ready, child_stop])
    while not pathlib.Path(child_ready).exists():
        time.sleep(0.01)
    if os.environ.get('TEST_IGNORE_TERM'):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    state_path.write_text(json.dumps({'pid':os.getpid(), 'child':child.pid, 'config':os.environ.get('DOCKER_CONFIG')}))
    time.sleep(60)
if name == 'aws' and args[1] == 'get-login-password':
    print('synthetic-token')
if name == 'aws' and args[1] == 'describe-images':
    print(os.environ['TEST_DIGEST'])
if name == 'docker' and args[0] == 'login':
    sys.stdin.read()
if name == 'docker' and args[:2] == ['image', 'inspect']:
    previous = [json.loads(line) for line in pathlib.Path(os.environ['TEST_CALLS']).read_text().splitlines()]
    count = sum(call[:3] == ['docker','image','inspect'] for call in previous)
    print('sha256:' + 'd' * 64 if os.environ.get('TEST_MUTATE_TAG') and count > 1 else os.environ['TEST_IMAGE_ID'])
'''.replace("PYTHON", sys.executable, 1)
        for name in ["aws", "docker"]:
            target = binary_directory / name
            target.write_text(fake_tool)
            target.chmod(0o700)
        self.environment = {
            "PATH": f"{binary_directory}:{Path(sys.executable).parent}:/usr/bin:/bin",
            "AWS_REGION": "us-east-1", "ECR_REGISTRY": "123456789012.dkr.ecr.us-east-1.amazonaws.com",
            "ECR_REPOSITORY": "synthetic/app", "IMAGE_COMPONENT": "app", "IMAGE_TARGET": "runtime",
            "IMAGE_PLATFORM": "linux/amd64", "CI_JOB_ID": "1", "CI_PIPELINE_ID": "42",
            "CI_COMMIT_SHA": SHA, "CI_COMMIT_SHORT_SHA": SHA[:8], "CI_IMAGE_SMOKE_COMMAND": "true",
            "CI_IMAGE_SCAN_COMMAND": 'printf "%s\\n" synthetic-scan > "$CI_SCAN_REPORT_DIR/report.txt"',
            "CI_PIPELINE_SOURCE": "push", "CI_COMMIT_REF_PROTECTED": "true",
            "CI_COMMIT_BRANCH": "release/test", "EXPECTED_IMAGE_SPECS": json.dumps({"app": SPECS["app"]}),
            "CI_COMMAND_STOP_SECONDS": "1", "TEST_IMAGE_ID": IMAGE_ID,
            "TMPDIR": str(self.root),
            "TEST_CALLS": str(self.root / "calls.jsonl"), "TEST_DIGEST": DIGEST,
        }

    def run_build(self, updates):
        environment = {**self.environment, **updates}
        self.verify_fake_tools(environment)
        call_path = self.root / "calls.jsonl"
        call_path.unlink(missing_ok=True)
        shutil.rmtree(self.root / "security-reports", ignore_errors=True)
        result = subprocess.run(["/bin/bash", str(ASSETS / "build-image.sh")], cwd=self.root,
                                env=environment, text=True, capture_output=True, timeout=15)
        calls = [json.loads(line) for line in call_path.read_text().splitlines()] if call_path.exists() else []
        record_path = self.root / "build-results/app-1.json"
        record = json.loads(record_path.read_text()) if record_path.exists() else None
        return result, calls, record

    def verify_fake_tools(self, environment):
        for name in ("aws", "docker", "rm"):
            expected = self.root / "bin" / name
            if name == "rm" and not expected.exists():
                continue
            resolved = shutil.which(name, path=environment["PATH"])
            if not expected.is_file() or not os.access(expected, os.X_OK) or resolved != str(expected):
                raise RuntimeError(f"测试替身不可执行或解析路径错配：{name}")

    def test_nonexecutable_or_misresolved_fake_never_falls_back_to_real_tool(self):
        fake = self.root / "bin/docker"
        fake.chmod(0o600)
        with self.assertRaises(RuntimeError):
            self.run_build({})
        fake.chmod(0o700)
        with self.assertRaises(RuntimeError):
            self.run_build({"PATH": "/usr/bin:/bin"})
        self.assertFalse((self.root / "calls.jsonl").exists())

    def test_invalid_retry_budget_stops_before_external_tools(self):
        for value in ["0", "6", "-1", "abc", ""]:
            with self.subTest(value=value):
                result, calls, record = self.run_build({"CI_ECR_DIGEST_ATTEMPTS": value})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertEqual(record["stage"], "preflight")
                self.assertEqual(record["status"], "failed")

    def test_invalid_or_missing_secret_mapping_stops_before_external_tools(self):
        for value in ["id=x,env=TOKEN;invalid", "id=x,env=MISSING_TOKEN"]:
            with self.subTest(value=value):
                result, calls, record = self.run_build({"CI_BUILD_SECRETS": value})
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertEqual(record["stage"], "preflight")

    def test_default_and_valid_retry_budgets_can_deliver(self):
        for updates in [{}, {"CI_ECR_DIGEST_ATTEMPTS": "1"}, {"CI_ECR_DIGEST_ATTEMPTS": "5"}]:
            with self.subTest(updates=updates):
                result, calls, record = self.run_build(updates)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(["docker", "push", record["image_uri"]], calls)
                self.assertEqual(record["status"], "pushed")
                self.assertEqual(record["digest"], DIGEST)

    def test_valid_secret_mapping_reaches_build_without_exposing_value(self):
        result, calls, record = self.run_build({
            "CI_BUILD_SECRETS": "id=npm_token,env=NPM_TOKEN", "NPM_TOKEN": "synthetic-private-value",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        build = next(call for call in calls if call[:2] == ["docker", "build"])
        index = build.index("--secret")
        self.assertEqual(build[index + 1], "id=npm_token,env=NPM_TOKEN")
        self.assertNotIn("synthetic-private-value", json.dumps(calls) + json.dumps(record) + result.stdout + result.stderr)

    def test_smoke_failure_preserves_exit_code_and_blocks_push(self):
        result, calls, record = self.run_build({"CI_IMAGE_SMOKE_COMMAND": "exit 17"})
        self.assertEqual(result.returncode, 17)
        self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))
        self.assertEqual(record["stage"], "smoke")
        self.assertEqual(record["exit_code"], 17)

    def test_scan_failure_blocks_push(self):
        result, calls, record = self.run_build({"CI_IMAGE_SCAN_COMMAND": "exit 23"})
        self.assertEqual(result.returncode, 23)
        self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))
        self.assertEqual(record["stage"], "image_scan")

    def test_untrusted_publish_context_stops_before_external_tools(self):
        for updates in ({"CI_COMMIT_REF_PROTECTED": "false"}, {"CI_PIPELINE_SOURCE": "merge_request_event"},
                        {"CI_PIPELINE_SOURCE": "schedule"}, {"CI_COMMIT_BRANCH": "develop"}):
            with self.subTest(updates=updates):
                result, calls, record = self.run_build(updates)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertEqual(record["stage"], "preflight")

    def test_manifest_target_region_and_budgets_are_checked_before_login(self):
        for updates in ({"IMAGE_TARGET": "other"}, {"IMAGE_PLATFORM": "linux/arm64"},
                        {"AWS_REGION": "eu-west-1"}, {"CI_COMMAND_TIMEOUT_SECONDS": "0"},
                        {"CI_COMMAND_STOP_SECONDS": "61"}, {"CI_IMAGE_SCAN_COMMAND": ""}):
            with self.subTest(updates=updates):
                result, calls, _ = self.run_build(updates)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])

    def test_required_check_records_are_validated_before_external_operations(self):
        for filename in ("verify-exit-code.txt", "source-scan-exit-code.txt"):
            path = self.root / filename
            for content in (None, "19\n", "0\x00", "0" * 20):
                with self.subTest(filename=filename, content=content):
                    path.unlink(missing_ok=True)
                    if content is not None:
                        path.write_text(content)
                    result, calls, record = self.run_build({})
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(calls, [])
                    self.assertEqual(record["stage"], "preflight")
            path.write_text("0\n")

    def test_tool_stage_failures_preserve_status_and_push_uncertainty(self):
        for stage in ("ecr_login", "build", "inspect", "push", "resolve_digest"):
            with self.subTest(stage=stage):
                result, calls, record = self.run_build({"TEST_FAIL_STAGE": stage, "CI_ECR_DIGEST_ATTEMPTS": "1"})
                self.assertEqual(result.returncode, 27)
                self.assertEqual(record["stage"], stage)
                self.assertEqual(record["push_state"], "unknown" if stage in {"push", "resolve_digest"} else "not_attempted")
                if stage not in {"push", "resolve_digest"}:
                    self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))

    def test_scan_requires_fresh_report_and_binds_local_image_identity(self):
        result, _, _ = self.run_build({})
        self.assertEqual(result.returncode, 0, result.stderr)
        identity = json.loads((self.root / "security-reports/image/app/scan-context.json").read_text())
        self.assertEqual(identity["image_id"], IMAGE_ID)
        self.assertEqual(identity["commit_sha"], SHA)
        result, calls, record = self.run_build({"CI_IMAGE_SCAN_COMMAND": "true"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(record["stage"], "image_scan")
        self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))

    def test_tag_change_after_scan_blocks_push(self):
        result, calls, record = self.run_build({"TEST_MUTATE_TAG": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(record["stage"], "verify_image")
        self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))

    def test_invalid_digest_is_unknown_not_not_uploaded(self):
        result, _, record = self.run_build({"TEST_DIGEST": "not-a-digest", "CI_ECR_DIGEST_ATTEMPTS": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(record["push_state"], "unknown")
        self.assertEqual(record["digest"], "")

    def test_record_failure_does_not_replace_original_failure(self):
        (self.root / "scripts/ci/build-record.py").write_text("import sys\nif '--preflight' not in sys.argv: sys.exit(9)\n")
        result, calls, _ = self.run_build({"CI_IMAGE_SMOKE_COMMAND": "exit 17"})
        self.assertEqual(result.returncode, 17)
        self.assertFalse(any(call[:2] == ["docker", "push"] for call in calls))
        result, _, _ = self.run_build({})
        self.assertNotEqual(result.returncode, 0)

    def test_authentication_cleanup_failure_keeps_original_error_and_remote_digest(self):
        fake_rm = self.root / "bin/rm"
        fake_rm.write_text("#!/bin/sh\nexit 31\n")
        fake_rm.chmod(0o700)
        result, _, record = self.run_build({"CI_IMAGE_SMOKE_COMMAND": "exit 17"})
        self.assertEqual(result.returncode, 17)
        self.assertEqual(record["exit_code"], 17)
        self.assertIn("无法清理", result.stderr)
        result, _, record = self.run_build({})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(record["stage"], "cleanup")
        self.assertEqual(record["push_state"], "confirmed")
        self.assertEqual(record["digest"], DIGEST)

    def test_term_cleans_authentication_and_owned_command_descendants(self):
        for stage in ("build", "push"):
            with self.subTest(stage=stage):
                state_path = self.root / f"{stage}-state.json"
                self.verify_fake_tools(self.environment)
                process = subprocess.Popen(["/bin/bash", str(ASSETS / "build-image.sh")], cwd=self.root,
                                           env={**self.environment, "TEST_HOLD_STAGE": stage, "TEST_STATE": str(state_path),
                                                "TEST_IGNORE_TERM": "1", "PYTHONDONTWRITEBYTECODE": "1"},
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
                try:
                    deadline = time.monotonic() + 8
                    while not state_path.exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertTrue(state_path.exists())
                    state = json.loads(state_path.read_text())
                    process.send_signal(signal.SIGTERM)
                    _, stderr = process.communicate(timeout=8)
                    self.assertEqual(process.returncode, 143, stderr)
                    self.assertFalse(Path(state["config"]).exists())
                    self.assertTrue(Path(str(state_path) + ".child-stopped").exists())
                    record = json.loads((self.root / "build-results/app-1.json").read_text())
                    self.assertEqual(record["stage"], stage)
                    self.assertEqual(record["exit_code"], 143)
                    self.assertEqual(record["push_state"], "unknown" if stage == "push" else "not_attempted")
                finally:
                    if state_path.exists():
                        state = json.loads(state_path.read_text())
                        try:
                            os.killpg(state["pid"], signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    process.communicate(timeout=3)
                shutil.rmtree(self.root / "security-reports", ignore_errors=True)


class CommandLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bootstrap-command-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def invoke(self, code, *options):
        return subprocess.run([sys.executable, str(ASSETS / "run-command.py"), "--timeout", "1", "--grace", "1",
                               *options, "--", sys.executable, "-c", code], cwd=self.root,
                              env={**os.environ, "CI_COMMIT_SHA": SHA, "CI_PIPELINE_ID": "42"},
                              capture_output=True, text=True, timeout=5)

    def test_exit_status_and_signal_propagate(self):
        for code, expected in (("pass", 0), ("raise SystemExit(29)", 29),
                               ("import os,signal; os.kill(os.getpid(), signal.SIGTERM)", 143)):
            with self.subTest(expected=expected):
                self.assertEqual(self.invoke(code).returncode, expected)

    def test_timeout_stops_uncooperative_command_within_budget(self):
        start = time.monotonic()
        result = self.invoke("import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)")
        self.assertEqual(result.returncode, 124)
        self.assertLess(time.monotonic() - start, 4.5)

    def test_main_exit_does_not_hide_uncooperative_descendant(self):
        code = ("import os,pathlib,subprocess,sys,time; pathlib.Path('group').write_text(str(os.getpid())); "
                "subprocess.Popen([sys.executable,'-c',\"import pathlib,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path('child-ready').touch(); time.sleep(60)\"]); "
                "exec(\"while not pathlib.Path('child-ready').exists(): time.sleep(0.01)\")")
        try:
            result = self.invoke(code)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("兜底清理", result.stderr)
        finally:
            if (self.root / "group").exists():
                try:
                    os.killpg(int((self.root / "group").read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_scan_report_requires_fresh_nonempty_output(self):
        directory = self.root / "reports"
        directory.mkdir()
        (directory / "old.txt").write_text("old")
        result = self.invoke("raise SystemExit(0)", "--report-directory", str(directory))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((directory / "old.txt").read_text(), "old")
        result = self.invoke("pass", "--report-directory", "empty")
        self.assertNotEqual(result.returncode, 0)
        code = "import os,pathlib; pathlib.Path(os.environ['CI_SCAN_REPORT_DIR'],'raw.json').write_text('{}')"
        result = self.invoke(code, "--report-directory", "current")
        self.assertEqual(result.returncode, 0, result.stderr)
        identity = json.loads((self.root / "current/scan-context.json").read_text())
        self.assertEqual(identity["commit_sha"], SHA)
        self.assertEqual(identity["exit_code"], 0)

    def test_cancel_during_spawn_handoff_is_not_lost(self):
        spec = importlib.util.spec_from_file_location("bootstrap_command", ASSETS / "run-command.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        original = subprocess.Popen
        target_started = []

        def spawn(*args, **kwargs):
            process = original(*args, **kwargs)
            if args[0][0] == sys.executable:
                target_started.append(process.pid)
                os.kill(os.getpid(), signal.SIGTERM)
            return process

        with patch.object(runner.subprocess, "Popen", spawn):
            result = runner.run([sys.executable, "-c", "import time; time.sleep(60)"], 3, 1)
        self.assertEqual(result, 143)
        self.assertEqual(len(target_started), 1)

    def test_process_query_failure_stops_before_starting_target(self):
        spec = importlib.util.spec_from_file_location("bootstrap_command_probe", ASSETS / "run-command.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        bad_ps = self.root / "ps"
        marker = self.root / "target-started"
        command = [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"]
        for output in ("", "not a process snapshot", "1 2 Z"):
            bad_ps.write_text(f"#!{sys.executable}\nprint({output!r})\n")
            bad_ps.chmod(0o700)
            with self.subTest(output=output), patch.object(runner.sys, "platform", "darwin"), \
                    patch.object(runner.shutil, "which", return_value=str(bad_ps)):
                with self.assertRaises(ValueError):
                    runner.run(command, 1, 1)
            self.assertFalse(marker.exists())
        with patch.object(runner.sys, "platform", "darwin"), patch.object(runner.shutil, "which", return_value=None):
            with self.assertRaises(ValueError):
                runner.run(command, 1, 1)
        self.assertFalse(marker.exists())

    def test_cleanup_query_failure_preserves_command_failure(self):
        spec = importlib.util.spec_from_file_location("bootstrap_command_cleanup_probe", ASSETS / "run-command.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        for exit_code in (0, 29):
            with self.subTest(exit_code=exit_code), \
                    patch.object(runner, "group_has_running_processes", side_effect=[True, ValueError("synthetic")]), \
                    patch.object(runner.os, "killpg"):
                result = runner.run([sys.executable, "-c", f"raise SystemExit({exit_code})"], 1, 1)
            self.assertEqual(result, exit_code or 1)

    def test_unknown_posix_state_remains_active(self):
        spec = importlib.util.spec_from_file_location("bootstrap_command_unknown_state", ASSETS / "run-command.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        for state, active in (("?E", True), ("?", True), ("S", True), ("Z", False)):
            output = f"{os.getpid()} {os.getpgrp()} S\n999999 999999 {state}\n"
            snapshot = subprocess.CompletedProcess([], 0, output, "")
            with self.subTest(state=state), patch.object(runner.sys, "platform", "darwin"), \
                    patch.object(runner.shutil, "which", return_value="/synthetic/ps"), \
                    patch.object(runner.subprocess, "run", return_value=snapshot):
                self.assertEqual(runner.group_has_running_processes(999999), active)


@unittest.skipUnless(sys.platform.startswith("linux"), "需要 Linux 的 /proc 和 subreaper")
class LinuxCommandLifecycleTests(unittest.TestCase):
    def exercise(self, mode):
        # 独立监督进程接管孤儿，刻意延后 wait，保证僵尸不会被容器 PID 1 提前回收。
        child = textwrap.dedent('''
            import os, pathlib, signal, sys, time
            pathlib.Path('owned-group').write_text(str(os.getpid()))
            mode = sys.argv[1]
            if mode in ('zombie', 'mixed'):
                pid = os.fork()
                if pid == 0:
                    os._exit(0)
                pathlib.Path('zombie-pid').write_text(str(pid))
                deadline = time.monotonic() + 2
                while pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z':
                    if time.monotonic() > deadline:
                        raise RuntimeError('未形成受控僵尸')
                    time.sleep(0.01)
            if mode in ('graceful', 'mixed'):
                pid = os.fork()
                if pid == 0:
                    if mode == 'mixed':
                        signal.signal(signal.SIGTERM, signal.SIG_IGN)
                    else:
                        def stop(*_):
                            pathlib.Path('child-stopped').touch()
                            os._exit(0)
                        signal.signal(signal.SIGTERM, stop)
                    pathlib.Path('child-ready').touch()
                    while True:
                        time.sleep(1)
                pathlib.Path('live-pid').write_text(str(pid))
                deadline = time.monotonic() + 2
                while not pathlib.Path('child-ready').exists():
                    if time.monotonic() > deadline:
                        raise RuntimeError('后代未准备好')
                    time.sleep(0.01)
        ''')
        supervisor = textwrap.dedent('''
            import ctypes, json, os, pathlib, signal, subprocess, sys, time
            if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
                raise RuntimeError('不能启用测试 subreaper')
            try:
                result = subprocess.run([sys.executable, sys.argv[1], '--timeout', '4', '--grace', '1',
                                         '--', sys.executable, '-c', sys.argv[3], sys.argv[2]],
                                        capture_output=True, text=True, timeout=8)
                states = {}
                for name in ('zombie-pid', 'live-pid'):
                    if pathlib.Path(name).exists():
                        pid = int(pathlib.Path(name).read_text())
                        try:
                            states[name] = pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
                        except FileNotFoundError:
                            states[name] = 'gone'
                print(json.dumps({'code':result.returncode, 'stderr':result.stderr, 'states':states,
                                  'stopped':pathlib.Path('child-stopped').exists()}))
            finally:
                if pathlib.Path('owned-group').exists():
                    try:
                        os.killpg(int(pathlib.Path('owned-group').read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    try:
                        pid, _ = os.waitpid(-1, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if pid == 0:
                        time.sleep(0.01)
                else:
                    raise RuntimeError('测试监督进程未回收全部后代')
        ''')
        with tempfile.TemporaryDirectory(prefix="bootstrap-linux-command-") as temporary:
            result = subprocess.run([sys.executable, "-c", supervisor, str(ASSETS / "run-command.py"), mode, child],
                                    cwd=temporary, capture_output=True, text=True, timeout=12)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_unreaped_zombie_does_not_fail_successful_command(self):
        result = self.exercise("zombie")
        self.assertEqual(result["states"]["zombie-pid"], "Z")
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertNotIn("兜底清理", result["stderr"])

    def test_graceful_descendant_can_exit_without_being_reaped_yet(self):
        result = self.exercise("graceful")
        self.assertTrue(result["stopped"])
        self.assertEqual(result["states"]["live-pid"], "Z")
        self.assertEqual(result["code"], 0, result["stderr"])

    def test_zombie_does_not_hide_live_descendant_at_stop_deadline(self):
        result = self.exercise("mixed")
        self.assertEqual(result["states"]["zombie-pid"], "Z")
        self.assertNotEqual(result["code"], 0)
        self.assertIn("兜底清理", result["stderr"])
        self.assertIn(result["states"]["live-pid"], ("Z", "gone"))


class CiScriptTests(unittest.TestCase):
    def test_actual_template_blocks_preserve_failure_and_reject_missing_commands(self):
        # 只提取本模板明确使用的单个 literal script block；YAML 解析及平台语义另行验收。
        source = (ASSETS / "gitlab-ci.yml").read_text()
        cases = [("verify", "true", 0), ("verify", "exit 17", 17), ("verify", "printf synthetic | false", 1),
                 ("verify", None, 1), ("verify", "   ", 1),
                 ("source-scan", 'printf synthetic > "$CI_SCAN_REPORT_DIR/report.txt"', 0),
                 ("source-scan", "exit 23", 23), ("source-scan", "true", 1), ("source-scan", None, 1)]
        for name, command, expected in cases:
            with self.subTest(name=name, command=command), tempfile.TemporaryDirectory(prefix="bootstrap-ci-block-") as directory:
                body = re.search(rf"^{name}:\n(.*?)(?=^\S|\Z)", source, re.M | re.S).group(1)
                block = re.search(r"^  script:\n    - \|\n((?:^      .*\n|^ *\n)+)", body, re.M).group(1)
                root = Path(directory)
                (root / "scripts/ci").mkdir(parents=True)
                shutil.copy(ASSETS / "run-command.py", root / "scripts/ci/run-command.py")
                environment = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "CI_COMMIT_SHA": SHA,
                               "CI_PIPELINE_ID": "42", "CI_COMMAND_TIMEOUT_SECONDS": "5", "CI_COMMAND_STOP_SECONDS": "1"}
                if command is not None:
                    environment["CI_VERIFY_COMMAND" if name == "verify" else "CI_SOURCE_SCAN_COMMAND"] = command
                result = subprocess.run(["/bin/bash", "-euo", "pipefail", "-c", textwrap.dedent(block)], cwd=root,
                                        env=environment, capture_output=True, text=True, timeout=8)
                self.assertEqual(result.returncode, expected, result.stderr)
                codefile = "verify-exit-code.txt" if name == "verify" else "source-scan-exit-code.txt"
                self.assertEqual((root / codefile).read_text().strip(), str(expected))


if __name__ == "__main__":
    unittest.main()
