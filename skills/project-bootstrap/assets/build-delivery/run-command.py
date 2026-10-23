#!/usr/bin/env python3
"""Linux／POSIX Runner 的有界命令入口；取消只清理本次创建的会话进程组。"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


def group_has_running_processes(group_id):
    """检查活动成员；僵尸交由实际父进程回收，状态不可读不能当作已停止。"""
    members = []
    if sys.platform.startswith("linux"):
        # comm 可含空格和右括号，从最后一个右括号之后读取 state、ppid、pgrp。
        for directory in Path("/proc").iterdir():
            if not directory.name.isdecimal():
                continue
            try:
                tail = (directory / "stat").read_text(errors="replace").rsplit(")", 1)[1].split()
            except (FileNotFoundError, ProcessLookupError):
                continue  # 快照期间进程正常退出。
            except IndexError:
                raise ValueError("进程状态格式无效") from None
            if len(tail) < 3 or len(tail[0]) != 1:
                raise ValueError("进程状态格式无效")
            members.append((int(directory.name), int(tail[2]), tail[0]))
    else:
        ps = shutil.which("ps")
        if ps is None:
            raise ValueError("当前 POSIX 平台需要支持 pid、pgid、stat 输出的 ps")
        result = subprocess.run([ps, "-A", "-o", "pid=", "-o", "pgid=", "-o", "stat="],
                                capture_output=True, text=True, timeout=1,
                                env={"PATH": os.defpath, "LC_ALL": "C"})
        if result.returncode != 0:
            raise ValueError("无法查询进程状态")
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) != 3:
                raise ValueError("进程状态格式无效")
            # 部分 POSIX 快照含 ? 等瞬态状态；不能误当成僵尸或让无关行使查询失败。
            members.append((int(fields[0]), int(fields[1]), fields[2][0]))
    # 至少能看见自身，避免空扫描或不兼容工具输出被当作整组已停止。
    if not any(pid == os.getpid() and group == os.getpgrp() for pid, group, _ in members):
        raise ValueError("进程状态扫描范围不完整")
    return any(group == group_id and state not in ("Z", "X", "x") for _, group, state in members)


def run(command, timeout, grace, environment=None):
    cancelled = 0

    def request_stop(signum, _frame):
        nonlocal cancelled
        if not cancelled:
            cancelled = 128 + signum

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    process = None
    result = None
    try:
        # 启动外部命令前确认查询能力；失败不降级为仅用 killpg(..., 0) 猜测存活。
        group_has_running_processes(os.getpgrp())
        if cancelled:
            return cancelled
        process = subprocess.Popen(command, start_new_session=True, env=environment)
        deadline = time.monotonic() + timeout
        while process.poll() is None and not cancelled and time.monotonic() < deadline:
            time.sleep(0.02)
        result = cancelled or (124 if process.poll() is None else process.returncode)
        # 主进程退出后仍清理同组后代；组内僵尸不等于仍在执行，回收由实际父进程／Runner 负责。
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        else:
            stop_at = time.monotonic() + grace
            while time.monotonic() < stop_at:
                process.poll()
                if not group_has_running_processes(process.pid):
                    break
                time.sleep(0.02)
            if group_has_running_processes(process.pid):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                else:
                    if result == 0:
                        result = 1
                        print("命令结束后作用域未按期释放，已执行兜底清理。", file=sys.stderr)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            return cancelled or 124
        result = cancelled or result
        return 128 - result if result < 0 else result
    except (OSError, ValueError, subprocess.TimeoutExpired):
        if result is None:
            raise
        # 查询失败仍进入 finally 的本次资源兜底，不能覆盖已有命令／取消根因。
        print("命令清理期间无法确认进程状态。", file=sys.stderr)
        result = cancelled or result
        return (128 - result if result < 0 else result) or 1
    finally:
        # 异常路径也不把本次子进程留在后台；SIGKILL／Runner 丢失需由外部执行器兜底。
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, required=True)
    parser.add_argument("--grace", type=int, required=True)
    parser.add_argument("--report-directory", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not 1 <= args.timeout <= 86400 or not 1 <= args.grace <= 60 or os.name != "posix":
        raise ValueError("命令或运行预算无效")
    environment = os.environ.copy()
    identity = None
    if args.report_directory is not None:
        sha, pipeline, image_id = (environment.get(key, "") for key in ("CI_COMMIT_SHA", "CI_PIPELINE_ID", "CI_IMAGE_ID"))
        if (not re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", sha)
                or not re.fullmatch(r"[1-9][0-9]*", pipeline)
                or (image_id and not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id))):
            raise ValueError("扫描对象身份无效")
        # 每次使用全新输出目录，防止旧报告使未执行的扫描看似成功。
        args.report_directory.mkdir(parents=True, exist_ok=False)
        environment["CI_SCAN_REPORT_DIR"] = str(args.report_directory.resolve())
        identity = {"schema_version": 1, "commit_sha": sha, "pipeline_id": pipeline, "image_id": image_id}
    result = run(command, args.timeout, args.grace, environment)
    if identity is not None:
        try:
            reports = [path for path in args.report_directory.rglob("*")
                       if path.name != "scan-context.json" and path.is_file() and not path.is_symlink() and path.stat().st_size > 0]
            if result == 0 and not reports:
                result = 1
                print("扫描未产生本次非空报告。", file=sys.stderr)
            identity["exit_code"] = result
            (args.report_directory / "scan-context.json").write_text(json.dumps(identity) + "\n", encoding="utf-8")
        except OSError:
            print("扫描报告校验或身份记录失败。", file=sys.stderr)
            return result or 1
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        print("命令执行入口失败。", file=sys.stderr)
        sys.exit(1)
