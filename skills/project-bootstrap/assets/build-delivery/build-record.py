#!/usr/bin/env python3
"""只记录非秘密 CI 元信息，不读取或导出整个环境。"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from delivery_contract import SCHEMA_VERSION, expected_specs, validate_record, verification_status


def make_record(status, stage, exit_code, digest):
    component = os.environ.get("IMAGE_COMPONENT", "unknown")
    job_id = os.environ.get("CI_JOB_ID", "unknown")
    record = {
        "schema_version": SCHEMA_VERSION,
        "component": component,
        "target": os.environ.get("IMAGE_TARGET", ""),
        "platform": os.environ.get("IMAGE_PLATFORM", ""),
        "commit_sha": os.environ.get("CI_COMMIT_SHA", ""),
        "pipeline_id": os.environ.get("CI_PIPELINE_ID", ""),
        "job_id": job_id,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "image_uri": os.environ.get("CI_IMAGE_URI", ""),
        "tag": os.environ.get("CI_IMAGE_TAG", ""),
        "image_id": os.environ.get("CI_IMAGE_ID", ""),
        "digest": digest,
        "push_state": os.environ.get("CI_PUSH_STATE", "not_attempted"),
        "status": status,
        "stage": stage,
        "exit_code": exit_code,
    }
    return validate_record(record)


def write_record(status, stage, exit_code, digest, directory=Path("build-results")):
    record = validate_record(make_record(status, stage, exit_code, digest), specs=expected_specs())
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f'{record["component"]}-{record["job_id"]}.json'
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--status", choices=["failed", "pushed"], default="failed")
    parser.add_argument("--stage", default="preflight")
    parser.add_argument("--exit-code", type=int, default=1)
    parser.add_argument("--digest", default="")
    args = parser.parse_args()
    if args.preflight:
        validate_record(make_record("failed", "preflight", 1, ""), specs=expected_specs())
        for filename in ("verify-exit-code.txt", "source-scan-exit-code.txt"):
            if verification_status(filename=filename) != "passed":
                raise ValueError("缺少必需验证或源码扫描成功结果")
    else:
        write_record(args.status, args.stage, args.exit_code, args.digest)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, RecursionError):
        print("交付记录校验或保存失败。", file=sys.stderr)
        sys.exit(1)
