#!/usr/bin/env python3
"""汇总真实交付结果，再发送有界飞书通知；通知失败不改写交付记录。"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from delivery_contract import SCHEMA_VERSION, expected_specs, matches, parse_json, validate_record, verification_status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_image_record(path, specs=None):
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError("镜像记录文件无效")
    return validate_record(parse_json(path.read_text(encoding="utf-8")), path.name, specs)


def checked_context(outcome, errors):
    values = {key: os.environ.get(env, "") for key, env in (
        ("commit_sha", "CI_COMMIT_SHA"), ("pipeline_id", "CI_PIPELINE_ID"),
        ("pipeline_url", "CI_PIPELINE_URL"), ("ref", "CI_COMMIT_REF_NAME"), ("project", "CI_PROJECT_PATH"))}
    project_url = os.environ.get("CI_PROJECT_URL", "")
    try:
        parsed = urlsplit(project_url)
    except ValueError:
        parsed = urlsplit("")
    valid_url = (parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.query and not parsed.fragment
                 and not any(unicodedata.category(char).startswith("C") or char.isspace() for char in project_url))
    validations = {
        "commit_sha": matches(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", values["commit_sha"]),
        "pipeline_id": matches(r"[1-9][0-9]*", values["pipeline_id"]),
        "pipeline_url": valid_url and values["pipeline_url"] == f'{project_url}/-/pipelines/{values["pipeline_id"]}',
        "ref": bool(values["ref"]) and len(values["ref"]) <= 255 and not any(
            unicodedata.category(char).startswith("C") for char in values["ref"]),
        "project": matches(r"[A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)+", values["project"])
                   and parsed.path.endswith("/" + values["project"]),
    }
    for key, valid in validations.items():
        if not valid:
            if outcome != "failure":
                raise ValueError("流水线上下文校验失败")
            values[key] = "unknown"
            errors.append(f"{key} 上下文校验失败")
    return values


def collect_result(outcome, root=Path(".")):
    errors = []
    context = checked_context(outcome, errors)
    specs = None
    try:
        specs = expected_specs()
    except (ValueError, RecursionError):
        if outcome != "failure":
            raise
        errors.append("预期镜像清单校验失败")
    components = list(specs) if specs is not None else []
    images = []
    for index, path in enumerate(sorted((root / "build-results").glob("*.json")), 1):
        try:
            item = read_image_record(path, specs)
            if any(previous["component"] == item["component"] for previous in images):
                raise ValueError("组件记录重复")
            images.append(item)
        except (OSError, ValueError, UnicodeError, RecursionError):
            if outcome != "failure":
                raise
            # 不转发损坏正文、文件名或异常文本，其他有效组件仍保留。
            errors.append(f"镜像记录 {index} 校验失败")
    checks = {}
    for key, filename in (("verification", "verify-exit-code.txt"), ("source_scan", "source-scan-exit-code.txt")):
        try:
            checks[key] = verification_status(root, filename)
        except (OSError, ValueError, UnicodeError):
            if outcome != "failure":
                raise
            checks[key] = "unknown"
            errors.append(f"{key} 退出记录校验失败")
    actual = [item.get("component") for item in images]
    complete = (
        not errors and all(value == "passed" for value in checks.values())
        and len(actual) == len(components)
        and set(actual) == set(components)
        and all(item["status"] == "pushed" for item in images)
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        **context,
        **checks,
        "status": "complete" if complete and outcome == "success" else "failed",
        "expected_components": components,
        "images": images,
    }
    if errors:
        result["collection_errors"] = errors
    (root / "build-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if outcome == "success" and not complete:
        raise ValueError("必需验证或镜像记录不完整，不能发送成功通知")
    return result


def make_payload(result):
    complete = result["status"] == "complete"
    title = "镜像构建及 ECR 推送成功" if complete else "验证或镜像交付失败"
    lines = [title, f"项目：{result['project']}", f"分支：{result['ref']}",
             f"提交：{result['commit_sha']}", f"验证：{result['verification']}，源码扫描：{result['source_scan']}",
             f"流水线：{result['pipeline_url']}"]
    lines.extend(result.get("collection_errors", [])[:20])
    for item in result["images"][:20]:
        lines.append(f"{item['component']}：{item.get('status')}，阶段：{item.get('stage')}")
        lines.append(f"推送状态：{item['push_state']}")
        if item.get("image_uri"):
            lines.append(item["image_uri"])
        if item.get("digest"):
            lines.append(item["digest"])
    if not result["images"]:
        lines.append("没有可用的镜像记录，请查看验证及构建 Job。")
    # 已有飞书卡片模板可在此替换载荷，保持结果判定及安全边界。
    payload = {"msg_type": "text", "content": {"text": "\n".join(lines)[:8000]}}
    while len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > 18000:
        text = payload["content"]["text"]
        payload["content"]["text"] = text[:len(text) * 3 // 4]
    return payload


def send_notice(payload, url, attempts=3, timeout=10, opener=None, sleep=time.sleep,
                secret="", clock=time.time):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"open.feishu.cn", "open.larksuite.com"}
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.query or parsed.fragment
            or not re.fullmatch(r"/open-apis/bot/v2/hook/[A-Za-z0-9-]+", parsed.path)):
        raise ValueError("飞书 Webhook 地址无效")
    if not 1 <= attempts <= 5 or not 1 <= timeout <= 120:
        raise ValueError("通知预算无效")
    opener = opener or build_opener(NoRedirect())
    for attempt in range(attempts):
        try:
            signed = dict(payload)
            if secret:
                timestamp = str(int(clock()))
                signature = hmac.new(f"{timestamp}\n{secret}".encode("utf-8"), digestmod=hashlib.sha256).digest()
                signed.update(timestamp=timestamp, sign=base64.b64encode(signature).decode("ascii"))
            body = json.dumps(signed, ensure_ascii=False).encode("utf-8")
            if len(body) > 20000:
                raise ValueError("通知载荷过大")
            request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with opener.open(request, timeout=timeout) as response:
                reply = json.loads(response.read(65536))
                code = reply.get("code", reply.get("StatusCode"))
                if type(code) is not int or code != 0:
                    raise ValueError("飞书返回业务失败")
            return
        except Exception:
            if attempt + 1 == attempts:
                # 不输出 URL、请求头、上游正文或异常文本，避免泄漏 Webhook。
                raise RuntimeError("飞书通知失败，交付记录已保留") from None
            sleep(min(attempt + 1, 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcome", choices=["success", "failure"], required=True)
    parser.add_argument("--collect-only", action="store_true", help="仅校验并生成交付记录，不发送通知")
    args = parser.parse_args()
    result = collect_result(args.outcome)
    if args.collect_only:
        return
    send_notice(make_payload(result), os.environ.get("FEISHU_WEBHOOK_URL", ""),
                attempts=int(os.environ.get("FEISHU_NOTIFY_ATTEMPTS", "3")),
                timeout=int(os.environ.get("FEISHU_NOTIFY_TIMEOUT_SECONDS", "10")),
                secret=os.environ.get("FEISHU_WEBHOOK_SECRET", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"通知 Job 未完成：{type(error).__name__}；请检查参数、交付记录和网络。", file=sys.stderr)
        sys.exit(1)
