"""交付记录的共享校验；只接受约定元信息，不把任意字段转发到汇总或通知。"""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path


COMPONENT = r"[a-z0-9][a-z0-9_.-]{0,63}"
TARGET = r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}"
PLATFORM = r"linux/(?:amd64|arm64)(?:/v[0-9]+)?"
REGISTRY = r"[0-9]{12}\.dkr\.ecr(?:-fips)?\.[a-z0-9-]+\.amazonaws\.com(?:\.cn)?"
REPOSITORY = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*(?:/[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*)*"
DIGEST = r"sha256:[a-f0-9]{64}"
STAGES = {"preflight", "ecr_login", "build", "inspect", "smoke", "image_scan", "verify_image", "push", "resolve_digest", "complete", "cleanup"}
FIELDS = {"schema_version", "component", "target", "platform", "commit_sha", "pipeline_id", "job_id", "built_at", "image_uri", "tag", "image_id", "digest", "push_state", "status", "stage", "exit_code"}
SCHEMA_VERSION = 2


def matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def parse_json(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("记录存在重复字段")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=unique_object)


def expected_specs():
    value = parse_json(os.environ.get("EXPECTED_IMAGE_SPECS", ""))
    if not isinstance(value, dict) or not value:
        raise ValueError("需要明确预期镜像清单")
    for component, spec in value.items():
        if (not matches(COMPONENT, component) or not isinstance(spec, dict)
                or set(spec) != {"repository", "target", "platform"}
                or not matches(REPOSITORY, spec["repository"])
                or not matches(TARGET, spec["target"]) or not matches(PLATFORM, spec["platform"])):
            raise ValueError("预期镜像清单无效")
    return value


def verification_status(root=Path("."), filename="verify-exit-code.txt"):
    path = root / filename
    if not path.exists():
        return "unknown"
    if path.is_symlink() or path.stat().st_size > 16:
        raise ValueError("验证退出记录无效")
    code = path.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"0|[1-9][0-9]{0,2}", code) or int(code) > 255:
        raise ValueError("验证退出记录无效")
    return "passed" if code == "0" else "failed"


def validate_record(item, filename=None, specs=None):
    if not isinstance(item, dict) or set(item) != FIELDS:
        raise ValueError("镜像记录结构无效")
    if (type(item["schema_version"]) is not int or item["schema_version"] != SCHEMA_VERSION
            or type(item["exit_code"]) is not int or not 0 <= item["exit_code"] <= 255
            or any(not isinstance(item[key], str) for key in FIELDS - {"schema_version", "exit_code"})):
        raise ValueError("镜像记录类型无效")
    if (not matches(COMPONENT, item["component"]) or not matches(r"[1-9][0-9]*", item["job_id"])
            or not matches(r"[1-9][0-9]*", item["pipeline_id"])
            or not matches(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", item["commit_sha"])
            or item["commit_sha"] != os.environ.get("CI_COMMIT_SHA")
            or item["pipeline_id"] != os.environ.get("CI_PIPELINE_ID")):
        raise ValueError("记录来源无效")
    if filename is not None and filename != f'{item["component"]}-{item["job_id"]}.json':
        raise ValueError("记录文件与构建 Job 不一致")
    if not matches(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\+00:00|Z)", item["built_at"]):
        raise ValueError("记录时间无效")
    if datetime.fromisoformat(item["built_at"].replace("Z", "+00:00")).utcoffset() != timedelta(0):
        raise ValueError("记录时间不是 UTC")
    if item["stage"] not in STAGES or item["status"] not in {"pushed", "failed"}:
        raise ValueError("记录状态无效")
    if item["status"] == "failed" and item["exit_code"] == 0:
        raise ValueError("失败记录不能使用成功退出码")
    partial = item["status"] == "failed" and item["stage"] == "preflight"
    for key, pattern in (("target", TARGET), ("platform", PLATFORM), ("image_id", DIGEST), ("digest", DIGEST)):
        if item[key] and not matches(pattern, item[key]):
            raise ValueError("记录字段无效")
    if not partial and (not item["target"] or not item["platform"]):
        raise ValueError("记录缺少构建目标")
    if item["stage"] in {"smoke", "image_scan", "verify_image", "push", "resolve_digest", "complete"} and not item["image_id"]:
        raise ValueError("记录缺少实际镜像身份")
    if bool(item["image_uri"]) != bool(item["tag"]):
        raise ValueError("镜像地址与 tag 缺项")
    repository = None
    if item["image_uri"]:
        uri = re.fullmatch(f'({REGISTRY})/({REPOSITORY}):([^:]+)', item["image_uri"])
        prefix = f'release-{item["component"]}-{item["job_id"]}-'
        if (not uri or not item["tag"].startswith(prefix) or uri[3] != item["tag"]
                or len(item["tag"]) > 128):
            raise ValueError("镜像地址与构建标识不一致")
        short_sha = item["tag"][len(prefix):]
        if not matches(r"[a-f0-9]{7,16}", short_sha) or not item["commit_sha"].startswith(short_sha):
            raise ValueError("镜像 tag 与提交不一致")
        registry, repository = uri[1], uri[2]
        if registry != os.environ.get("ECR_REGISTRY"):
            raise ValueError("镜像地址与预期仓库不一致")
    elif not partial:
        raise ValueError("记录缺少镜像地址")
    if specs is not None:
        spec = specs.get(item["component"])
        if (spec is None or item["target"] != spec["target"] or item["platform"] != spec["platform"]
                or (repository is not None and repository != spec["repository"])):
            raise ValueError("记录与预期镜像清单不一致")
    state = item["push_state"]
    if state not in {"not_attempted", "unknown", "confirmed"}:
        raise ValueError("推送状态无效")
    if state == "not_attempted" and (item["stage"] in {"push", "resolve_digest", "complete"} or item["digest"]):
        raise ValueError("推送阶段与状态不一致")
    if state == "unknown" and (item["stage"] not in {"push", "resolve_digest", "cleanup"} or item["digest"]):
        raise ValueError("未知推送状态无效")
    if state == "confirmed" and (not item["digest"] or item["stage"] not in {"complete", "cleanup"}):
        raise ValueError("确认推送缺少证据")
    if item["status"] == "pushed" and (item["exit_code"] != 0 or item["stage"] != "complete"
            or state != "confirmed" or not item["image_id"]):
        raise ValueError("交付成功条件不完整")
    return item
