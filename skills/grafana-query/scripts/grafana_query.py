#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import socket
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


CONFIG_PATH = Path.home() / ".config" / "grafana-query" / "config.json"


class UserError(Exception):
    def __init__(self, code: str, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.payload = payload or {}


def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def error_payload(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, **extra}}


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def load_config(config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path).expanduser() if config_path else CONFIG_PATH
    if not path.exists():
        return error_payload(
            "config_not_found",
            f"Grafana 配置文件不存在：{path}；默认配置文件名为 config.json",
            path=str(path),
            minimalExample={
                "defaultProfile": "prod",
                "profiles": {
                    "prod": {
                        "url": "https://grafana.example.com",
                        "datasourceUid": "prometheus-main",
                        "apiKey": "grafana-service-account-token",
                        "timeoutSeconds": 15,
                    }
                },
            },
        )
    try:
        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        return error_payload("config_json_invalid", f"Grafana 配置 JSON 解析失败：{exc}", path=str(path))
    if not isinstance(config, dict):
        return error_payload("config_invalid", "Grafana 配置根节点必须是 JSON object", path=str(path))
    return ok(config)


def _require_str(profile: dict[str, Any], key: str, profile_name: str) -> str:
    value = profile.get(key)
    if not isinstance(value, str) or not value.strip():
        raise UserError("profile_invalid", f"profile {profile_name} 缺少字符串字段 {key}", {"profile": profile_name})
    return value.strip()


def get_profile(config: dict[str, Any], profile_name: str | None) -> tuple[str, dict[str, Any]]:
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise UserError("profiles_missing", "配置缺少 profiles object")
    selected = profile_name or config.get("defaultProfile")
    if not isinstance(selected, str) or not selected:
        selected = next(iter(profiles.keys()))
    raw_profile = profiles.get(selected)
    if not isinstance(raw_profile, dict):
        raise UserError("profile_not_found", f"profile 不存在：{selected}", {"availableProfiles": sorted(profiles.keys())})
    profile = dict(raw_profile)
    profile["url"] = _require_str(profile, "url", selected).rstrip("/")
    profile["datasourceUid"] = _require_str(profile, "datasourceUid", selected)
    api_key = profile.get("apiKey")
    if api_key is not None and not isinstance(api_key, str):
        raise UserError("profile_invalid", f"profile {selected} 的 apiKey 必须是字符串", {"profile": selected})
    return selected, profile


def build_proxy_url(profile: dict[str, Any], api_path: str, params: dict[str, str] | None = None) -> str:
    path = api_path if api_path.startswith("/") else f"/{api_path}"
    base = f"{profile['url']}/api/datasources/proxy/uid/{profile['datasourceUid']}{path}"
    if not params:
        return base
    return f"{base}?{urlencode(params)}"


def redact(value: str, secret: str | None) -> str:
    if secret:
        return value.replace(secret, "***REDACTED***")
    return value


def parse_time(value: str, now: int | None = None) -> int:
    raw = value.strip()
    current = int(time.time()) if now is None else now
    match = re.fullmatch(r"-(\d+)([smhd])", raw)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        factor = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return current - amount * factor
    if re.fullmatch(r"\d+", raw):
        return int(raw)
    try:
        normalized = raw.replace("Z", "+00:00")
        return int(datetime.fromisoformat(normalized).timestamp())
    except ValueError as exc:
        raise UserError("time_invalid", f"无法解析时间参数：{value}", {"value": value}) from exc


def numeric_sample_pairs(values: list[list[Any]]) -> list[tuple[int, float]]:
    pairs: list[tuple[int, float]] = []
    for item in values:
        if not isinstance(item, list) or len(item) != 2:
            continue
        try:
            ts = int(float(item[0]))
            number = float(item[1])
        except (TypeError, ValueError):
            continue
        if not math.isfinite(number):
            continue
        pairs.append((ts, number))
    return pairs


def summarize_values(values: list[list[Any]]) -> dict[str, float | int | None]:
    pairs = numeric_sample_pairs(values)
    if not pairs:
        return {"min": None, "max": None, "avg": None, "last": None, "count": 0}
    nums = [number for _, number in pairs]
    return {
        "min": min(nums),
        "max": max(nums),
        "avg": sum(nums) / len(nums),
        "last": pairs[-1][1],
        "count": len(nums),
    }


def profile_timeout(profile: dict[str, Any]) -> float:
    raw = profile.get("timeoutSeconds", 15)
    return float(raw) if isinstance(raw, (int, float)) and raw > 0 else 15.0


def request_json(profile: dict[str, Any], api_path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    url = build_proxy_url(profile, api_path, params)
    headers = {"Accept": "application/json"}
    api_key = profile.get("apiKey")
    if isinstance(api_key, str) and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=profile_timeout(profile)) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            return data if isinstance(data, dict) else {"status": "error", "error": "response root is not object"}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise UserError(
            "grafana_http_error",
            f"Grafana HTTP 请求失败：{exc.code}",
            {"status": exc.code, "body": redact(body, api_key if isinstance(api_key, str) else None), "apiPath": api_path},
        ) from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise UserError("grafana_network_error", f"Grafana 网络请求失败：{exc}", {"apiPath": api_path}) from exc
    except json.JSONDecodeError as exc:
        raise UserError("grafana_json_invalid", f"Grafana 响应不是合法 JSON：{exc}", {"apiPath": api_path}) from exc


def ensure_prometheus_success(data: dict[str, Any]) -> Any:
    if data.get("status") == "success":
        return data.get("data")
    raise UserError(
        "prometheus_error",
        "Prometheus API 返回错误",
        {"errorType": data.get("errorType"), "error": data.get("error")},
    )


def filter_names(names: list[str], keywords: list[str], prefix: str | None, regex: str | None, limit: int) -> list[str]:
    result = list(names)
    if keywords:
        lowered = [k.lower() for k in keywords if k]
        result = [name for name in result if any(k in name.lower() for k in lowered)]
    if prefix:
        result = [name for name in result if name.startswith(prefix)]
    if regex:
        pattern = re.compile(regex)
        result = [name for name in result if pattern.search(name)]
    return result[:limit]


LABEL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SERIES_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def escape_promql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def parse_label_matchers(selector: list[str] | None, selector_re: list[str] | None) -> list[tuple[str, str, str]]:
    matchers: list[tuple[str, str, str]] = []
    for raw in selector or []:
        matchers.append(parse_label_matcher(raw, "="))
    for raw in selector_re or []:
        matchers.append(parse_label_matcher(raw, "=~"))
    return matchers


def parse_label_matcher(raw: str, operator: str) -> tuple[str, str, str]:
    if "=" not in raw:
        raise UserError("selector_invalid", f"selector 必须是 label=value 格式：{raw}", {"selector": raw})
    label, value = raw.split("=", 1)
    label = label.strip()
    value = value.strip()
    if not LABEL_NAME_RE.fullmatch(label):
        raise UserError("selector_invalid", f"selector label 名不合法：{label}", {"selector": raw})
    if value == "":
        raise UserError("selector_invalid", f"selector value 不能为空：{raw}", {"selector": raw})
    return label, operator, value


def build_label_selector(matchers: list[tuple[str, str, str]]) -> str:
    return ",".join(f'{label}{operator}"{escape_promql_string(value)}"' for label, operator, value in matchers)


def build_metric_selector(metric_name: str, matchers: list[tuple[str, str, str]] | None = None) -> str:
    matchers = matchers or []
    if not matchers:
        return metric_name
    selector = build_label_selector(matchers)
    return f"{metric_name}{{{selector}}}"


def load_selected_profile(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    loaded = load_config(args.config)
    if not loaded["ok"]:
        err = loaded["error"]
        raise UserError(err["code"], err["message"], {k: v for k, v in err.items() if k not in {"code", "message"}})
    return get_profile(loaded["data"], getattr(args, "profile", None))


def cmd_profiles(args: argparse.Namespace) -> dict[str, Any]:
    loaded = load_config(args.config)
    if not loaded["ok"]:
        return loaded
    config = loaded["data"]
    profiles = config.get("profiles", {})
    safe_profiles = {}
    if isinstance(profiles, dict):
        for name, profile in profiles.items():
            if isinstance(profile, dict):
                safe_profiles[name] = {
                    "url": str(profile.get("url", "")).rstrip("/"),
                    "datasourceUid": profile.get("datasourceUid"),
                    "timeoutSeconds": profile.get("timeoutSeconds", 15),
                }
    return ok({"defaultProfile": config.get("defaultProfile"), "profiles": safe_profiles})


def cmd_list_metrics(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    data = ensure_prometheus_success(request_json(profile, "/api/v1/label/__name__/values"))
    names = data if isinstance(data, list) else []
    filtered = filter_names(names, args.keyword or [], args.prefix, args.regex, args.limit)
    return ok({"profile": profile_name, "total": len(names), "count": len(filtered), "metricNames": filtered})


def cmd_metadata(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    params = {"metric": args.metric} if args.metric else None
    data = ensure_prometheus_success(request_json(profile, "/api/v1/metadata", params))
    metadata = data if isinstance(data, dict) else {}
    keys = filter_names(list(metadata.keys()), args.keyword or [], args.prefix, None, args.limit)
    return ok({"profile": profile_name, "count": len(keys), "metadata": {key: metadata[key] for key in keys}})


def cmd_labels(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    if args.metric:
        matchers = parse_label_matchers(getattr(args, "selector", []), getattr(args, "selector_re", []))
        params = {"match[]": build_metric_selector(args.metric, matchers)}
        if args.start:
            params["start"] = str(parse_time(args.start))
        if args.end:
            params["end"] = str(parse_time(args.end))
        series = ensure_prometheus_success(request_json(profile, "/api/v1/series", params))
        labels = sorted({key for item in series if isinstance(item, dict) for key in item.keys()})
    else:
        data = ensure_prometheus_success(request_json(profile, "/api/v1/labels"))
        labels = data if isinstance(data, list) else []
    return ok({"profile": profile_name, "metric": args.metric, "count": len(labels), "labels": labels[: args.limit]})


def cmd_label_values(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    matchers = parse_label_matchers(getattr(args, "selector", []), getattr(args, "selector_re", []))
    params: dict[str, str] = {}
    if args.metric:
        params["match[]"] = build_metric_selector(args.metric, matchers)
    if args.start:
        params["start"] = str(parse_time(args.start))
    if args.end:
        params["end"] = str(parse_time(args.end))
    if matchers:
        if not args.metric:
            raise UserError("metric_required", "使用 --selector 或 --selector-re 时必须指定 --metric")
        series = ensure_prometheus_success(request_json(profile, "/api/v1/series", params))
        values = sorted({str(item[args.label]) for item in series if isinstance(item, dict) and args.label in item})
    else:
        values = ensure_prometheus_success(request_json(profile, f"/api/v1/label/{args.label}/values", params))
        values = values if isinstance(values, list) else []
    return ok(
        {
            "profile": profile_name,
            "metric": args.metric,
            "selector": build_label_selector(matchers) if matchers else None,
            "label": args.label,
            "count": len(values),
            "values": values[: args.limit],
        }
    )


def _is_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def cmd_query(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    params = {"query": args.promql}
    if args.time:
        params["time"] = str(parse_time(args.time))
    response = request_json(profile, "/api/v1/query", params)
    if args.raw:
        return ok({"profile": profile_name, "raw": response})
    result = ensure_prometheus_success(response)
    series = result.get("result", []) if isinstance(result, dict) else []
    parsed = []
    for item in series:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        parsed.append(
            {
                "metric": item.get("metric", {}),
                "timestamp": value[0] if isinstance(value, list) and len(value) == 2 else None,
                "value": float(value[1]) if isinstance(value, list) and len(value) == 2 and _is_number(value[1]) else None,
            }
        )
    return ok({"profile": profile_name, "promql": args.promql, "count": len(parsed), "series": parsed})


def cmd_query_range(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    end = parse_time(args.end) if args.end else int(time.time())
    start = parse_time(args.start, now=end) if args.start else end - 3600
    params = {"query": args.promql, "start": str(start), "end": str(end), "step": str(args.step)}
    response = request_json(profile, "/api/v1/query_range", params)
    if args.raw:
        return ok({"profile": profile_name, "raw": response})
    result = ensure_prometheus_success(response)
    series = result.get("result", []) if isinstance(result, dict) else []
    parsed = []
    for item in series:
        if not isinstance(item, dict):
            continue
        values = item.get("values", [])
        parsed.append(
            {
                "metric": item.get("metric", {}),
                "summary": summarize_values(values if isinstance(values, list) else []),
            }
        )
    return ok(
        {
            "profile": profile_name,
            "promql": args.promql,
            "timeRange": {"start": start, "end": end, "step": args.step},
            "count": len(parsed),
            "series": parsed,
        }
    )


COUNTER_HINTS = ("_total", "_count", "_sum", "_bucket", "seconds_count", "requests_total")
COMMON_GROUP_LABELS = (
    "service",
    "application",
    "app",
    "job",
    "instance",
    "namespace",
    "pod",
    "uri",
    "route",
    "method",
    "status",
    "exception",
)


def build_promql_drafts(metric_name: str, labels: list[str], matchers: list[tuple[str, str, str]] | None = None) -> list[str]:
    group_labels = [label for label in COMMON_GROUP_LABELS if label in labels]
    if not group_labels:
        group_labels = labels[:3]
    is_counter = any(hint in metric_name for hint in COUNTER_HINTS)
    metric_expr = build_metric_selector(metric_name, matchers)
    drafts = []
    for label in group_labels[:5]:
        if is_counter:
            drafts.append(f"sum(rate({metric_expr}[5m])) by ({label})")
        else:
            drafts.append(f"avg({metric_expr}) by ({label})")
    if is_counter:
        drafts.insert(0, f"sum(rate({metric_expr}[5m]))")
    else:
        drafts.insert(0, f"avg({metric_expr})")
    return drafts


def labels_for_metric(
    profile: dict[str, Any],
    metric_name: str,
    start: str | None,
    end: str | None,
    matchers: list[tuple[str, str, str]] | None = None,
) -> list[str]:
    params = {"match[]": build_metric_selector(metric_name, matchers)}
    if start:
        params["start"] = str(parse_time(start))
    if end:
        params["end"] = str(parse_time(end))
    data = ensure_prometheus_success(request_json(profile, "/api/v1/series", params))
    return sorted({key for item in data if isinstance(item, dict) for key in item.keys()})


def cmd_discover(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    matchers = parse_label_matchers(getattr(args, "selector", []), getattr(args, "selector_re", []))
    metric_data = ensure_prometheus_success(request_json(profile, "/api/v1/label/__name__/values"))
    metric_names = metric_data if isinstance(metric_data, list) else []
    candidates = filter_names(metric_names, args.keyword or [], args.prefix, args.regex, args.limit)
    warnings = []
    try:
        metadata_response = request_json(profile, "/api/v1/metadata")
        metadata = ensure_prometheus_success(metadata_response)
        if not isinstance(metadata, dict):
            metadata = {}
    except UserError as exc:
        metadata = {}
        warnings.append(
            {
                "code": "metadata_unavailable",
                "message": "Prometheus metadata 不可用，已降级为仅基于指标名和 labels 发现。",
                "sourceCode": exc.code,
                **exc.payload,
            }
        )
    discovered = []
    for metric in candidates:
        labels = labels_for_metric(profile, metric, args.start, args.end, matchers)
        raw_meta = metadata.get(metric, [])
        discovered.append(
            {
                "metric": metric,
                "metadata": raw_meta[:3] if isinstance(raw_meta, list) else [],
                "labels": labels,
                "promqlDrafts": build_promql_drafts(metric, labels, matchers),
            }
        )
    payload = {
        "profile": profile_name,
        "selector": build_label_selector(matchers) if matchers else None,
        "count": len(discovered),
        "candidates": discovered,
    }
    if warnings:
        payload["warnings"] = warnings
    return ok(payload)


def parse_timeline_series(raw_series: list[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for raw in raw_series:
        if "=" not in raw:
            raise UserError("timeline_series_invalid", f"--series 必须是 name=promql 格式：{raw}", {"series": raw})
        name, promql = raw.split("=", 1)
        name = name.strip()
        promql = promql.strip()
        if not SERIES_NAME_RE.fullmatch(name):
            raise UserError("timeline_series_invalid", f"series 名只能包含字母、数字和下划线：{name}", {"series": raw})
        if not promql:
            raise UserError("timeline_series_invalid", f"series PromQL 不能为空：{raw}", {"series": raw})
        parsed.append((name, promql))
    return parsed


def query_range_values(profile: dict[str, Any], promql: str, start: int, end: int, step: int) -> tuple[dict[int, float], list[dict[str, Any]]]:
    params = {"query": promql, "start": str(start), "end": str(end), "step": str(step)}
    response = request_json(profile, "/api/v1/query_range", params)
    result = ensure_prometheus_success(response)
    series = result.get("result", []) if isinstance(result, dict) else []
    warnings = []
    if len(series) > 1:
        warnings.append({"code": "timeline_multi_series", "message": "PromQL 返回多条序列，仅使用第一条；请在 PromQL 中先聚合。"})
    if not series or not isinstance(series[0], dict):
        return {}, warnings
    values = series[0].get("values", [])
    return {ts: number for ts, number in numeric_sample_pairs(values if isinstance(values, list) else [])}, warnings


def render_timeline_markdown(rows: list[dict[str, Any]], names: list[str]) -> str:
    headers = ["time", *names]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---", *[":---:" for _ in names]]) + " |"]
    for row in rows:
        cells = [str(row["isoTime"])]
        for name in names:
            value = row.get(name)
            cells.append("" if value is None else f"{value:.6g}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def cmd_timeline(args: argparse.Namespace) -> dict[str, Any]:
    profile_name, profile = load_selected_profile(args)
    end = parse_time(args.end) if args.end else int(time.time())
    start = parse_time(args.start, now=end) if args.start else end - 3600
    series_defs = parse_timeline_series(args.series)
    timeline_values: dict[str, dict[int, float]] = {}
    warnings = []
    timestamps = set(range(start, end + 1, args.step))
    for name, promql in series_defs:
        values, series_warnings = query_range_values(profile, promql, start, end, args.step)
        timeline_values[name] = values
        timestamps.update(values.keys())
        for warning in series_warnings:
            warnings.append({"series": name, **warning})
    names = [name for name, _ in series_defs]
    rows = []
    for ts in sorted(timestamps):
        row: dict[str, Any] = {"time": ts, "isoTime": datetime.fromtimestamp(ts).isoformat()}
        for name in names:
            row[name] = timeline_values.get(name, {}).get(ts)
        rows.append(row)
    payload: dict[str, Any] = {
        "profile": profile_name,
        "timeRange": {"start": start, "end": end, "step": args.step},
        "series": [{"name": name, "promql": promql} for name, promql in series_defs],
        "rows": rows,
    }
    if args.format == "markdown":
        payload["markdown"] = render_timeline_markdown(rows, names)
    if warnings:
        payload["warnings"] = warnings
    return ok(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Prometheus metrics through Grafana datasource proxy.")
    parser.add_argument("--config", help="配置文件路径，默认 ~/.config/grafana-query/config.json")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("profiles", help="列出可用 profile，不输出 token")

    def add_profile_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("--profile", help="profile 名；不传则使用 defaultProfile")

    def add_selector_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--selector", action="append", default=[], help="精确 label matcher，格式 label=value，可重复")
        p.add_argument("--selector-re", action="append", default=[], help="正则 label matcher，格式 label=regex，可重复")

    list_metrics = subparsers.add_parser("list-metrics", help="列出指标名")
    add_profile_arg(list_metrics)
    list_metrics.add_argument("--keyword", action="append", default=[], help="关键词过滤，可重复")
    list_metrics.add_argument("--prefix", help="前缀过滤")
    list_metrics.add_argument("--regex", help="正则过滤")
    list_metrics.add_argument("--limit", type=int, default=100)

    metadata = subparsers.add_parser("metadata", help="查询指标 metadata")
    add_profile_arg(metadata)
    metadata.add_argument("--metric")
    metadata.add_argument("--keyword", action="append", default=[])
    metadata.add_argument("--prefix")
    metadata.add_argument("--limit", type=int, default=80)

    labels = subparsers.add_parser("labels", help="查询 label 名")
    add_profile_arg(labels)
    add_selector_args(labels)
    labels.add_argument("--metric")
    labels.add_argument("--start")
    labels.add_argument("--end")
    labels.add_argument("--limit", type=int, default=200)

    label_values = subparsers.add_parser("label-values", help="查询 label values")
    add_profile_arg(label_values)
    add_selector_args(label_values)
    label_values.add_argument("--metric")
    label_values.add_argument("--label", required=True)
    label_values.add_argument("--start")
    label_values.add_argument("--end")
    label_values.add_argument("--limit", type=int, default=200)

    query = subparsers.add_parser("query", help="执行 instant PromQL 查询")
    add_profile_arg(query)
    query.add_argument("--promql", required=True)
    query.add_argument("--time")
    query.add_argument("--raw", action="store_true")

    query_range = subparsers.add_parser("query-range", help="执行 range PromQL 查询")
    add_profile_arg(query_range)
    query_range.add_argument("--promql", required=True)
    query_range.add_argument("--start", default="-1h")
    query_range.add_argument("--end")
    query_range.add_argument("--step", type=int, default=60)
    query_range.add_argument("--raw", action="store_true")

    discover = subparsers.add_parser("discover", help="按关键词发现指标、labels 和 PromQL 草案")
    add_profile_arg(discover)
    add_selector_args(discover)
    discover.add_argument("--keyword", action="append", default=[], help="关键词过滤，可重复")
    discover.add_argument("--prefix")
    discover.add_argument("--regex")
    discover.add_argument("--start", default="-1h")
    discover.add_argument("--end")
    discover.add_argument("--limit", type=int, default=10)

    timeline = subparsers.add_parser("timeline", help="按同一时间窗口对齐多条 PromQL 序列")
    add_profile_arg(timeline)
    timeline.add_argument("--series", action="append", required=True, help="时间线序列，格式 name=promql，可重复")
    timeline.add_argument("--start", default="-1h")
    timeline.add_argument("--end")
    timeline.add_argument("--step", type=int, default=60)
    timeline.add_argument("--format", choices=["json", "markdown"], default="json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "profiles":
            print_json(cmd_profiles(args))
            return 0
        if args.command == "list-metrics":
            print_json(cmd_list_metrics(args))
            return 0
        if args.command == "metadata":
            print_json(cmd_metadata(args))
            return 0
        if args.command == "labels":
            print_json(cmd_labels(args))
            return 0
        if args.command == "label-values":
            print_json(cmd_label_values(args))
            return 0
        if args.command == "query":
            print_json(cmd_query(args))
            return 0
        if args.command == "query-range":
            print_json(cmd_query_range(args))
            return 0
        if args.command == "discover":
            print_json(cmd_discover(args))
            return 0
        if args.command == "timeline":
            print_json(cmd_timeline(args))
            return 0
        raise UserError("unknown_command", f"未知命令：{args.command}")
    except UserError as exc:
        print_json(error_payload(exc.code, str(exc), **exc.payload))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
