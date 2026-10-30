#!/usr/bin/env python3
"""cfast: Companion sample storage and one-command C++ testing on Linux."""

import argparse
import contextlib
import fcntl
import json
import math
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
HOME = Path(os.environ.get("CFAST_HOME", str(Path.home() / ".cf"))).expanduser()
TESTS = HOME / "tests"
MAX_BODY = 8 * 1024 * 1024
OUTPUT_LIMIT = 8 * 1024 * 1024
DEFAULT_TIMEOUT = 5.0
DEFAULT_MEMORY = 256.0


class ToolError(Exception):
    """An actionable error that should not show a Python traceback."""


def problem_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:gym)?[0-9]{1,12}[A-Z][0-9]{0,3}", value):
        raise ToolError(f"invalid problem ID: {value!r}; expected e.g. 1032D, 1234B1 or gym102001A")
    return value


def pid_from_url(url):
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https") or not (host == "codeforces.com" or host.endswith(".codeforces.com")):
        return None
    match = re.fullmatch(r"/(contest|gym)/([0-9]{1,12})/problem/([A-Za-z][0-9]{0,3})/?", parsed.path)
    if match:
        kind, contest, index = match.groups()
        return ("gym" if kind == "gym" else "") + contest + index.upper()
    match = re.fullmatch(r"/problemset/problem/([0-9]{1,12})/([A-Za-z][0-9]{0,3})/?", parsed.path)
    return match[1] + match[2].upper() if match else None


def positive(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("must be a positive finite number") from None
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return number


@contextlib.contextmanager
def problem_lock(pid, exclusive=True):
    locks = TESTS / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    with (locks / f"{problem_id(pid)}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield


def save_payload(data):
    if not isinstance(data, dict):
        raise ToolError("payload must be a JSON object")
    pid = pid_from_url(data.get("url"))
    if pid is None:
        raise ToolError(f"could not parse problem id from {data.get('url')!r}")
    samples = data.get("tests")
    if not isinstance(samples, list) or not all(
        isinstance(test, dict) and isinstance(test.get("input"), str)
        and isinstance(test.get("output"), str) for test in samples
    ):
        raise ToolError("tests must be an array of input/output string pairs")
    metadata = {key: data[key] for key in (
        "name", "url", "group", "interactive", "timeLimit", "memoryLimit", "testType", "input", "output"
    ) if key in data}
    for key in ("timeLimit", "memoryLimit"):
        if key in metadata:
            try:
                if isinstance(metadata[key], bool):
                    raise ValueError
                metadata[key] = positive(metadata[key])
            except (ValueError, argparse.ArgumentTypeError):
                raise ToolError(f"invalid {key}: must be positive and finite") from None
    with problem_lock(pid):
        destination = TESTS / pid
        with tempfile.TemporaryDirectory(prefix=".incoming-", dir=TESTS) as scratch:
            stage = Path(scratch) / pid
            stage.mkdir()
            for i, test in enumerate(samples, 1):
                (stage / f"{i}.in").write_text(test["input"], encoding="utf-8")
                (stage / f"{i}.out").write_text(test["output"], encoding="utf-8")
            (stage / "meta.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            if (destination / "custom").is_dir():
                shutil.copytree(destination / "custom", stage / "custom")
            backup = Path(scratch) / "previous"
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
            except OSError:
                if backup.exists():
                    backup.rename(destination)
                raise
    if data.get("interactive"):
        print("warning: interactive problems are unsupported; samples saved only", flush=True)
    print(f"saved {len(samples)} tests for {pid} ({data.get('name', 'unnamed')})", flush=True)
    return pid


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_POST(self):
        response = {"saved": False}
        try:
            self.connection.settimeout(3)
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
                raise ToolError("missing or invalid Content-Length")
            length = int(lengths[0])
            if not 0 < length <= MAX_BODY or self.headers.get("Transfer-Encoding"):
                raise ToolError("unsupported framing or payload exceeds 8 MiB")
            body = self.rfile.read(length)
            if len(body) != length:
                raise ToolError("incomplete request body")
            response = {"saved": True, "problem": save_payload(json.loads(body))}
        except (ToolError, ValueError, OSError) as error:
            response["error"] = str(error)
            print(f"skipped: {error}", flush=True)
        raw = (json.dumps(response) + "\n").encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass
        self.close_connection = True

    def log_message(self, *_):
        pass


def listen(port):
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"listening on http://127.0.0.1:{server.server_port} ...", flush=True)
        server.serve_forever()
    return 0


def new(pid):
    destination = Path.cwd() / f"{problem_id(pid)}.cpp"
    template = HOME / "template.cpp"
    if not template.is_file():
        template = ROOT / "template.cpp"
    try:
        with template.open("rb") as source, destination.open("xb") as output:
            shutil.copyfileobj(source, output)
    except FileExistsError:
        raise ToolError(f"already exists: {destination}; refusing to overwrite") from None
    print(f"created {destination}")
    return 0


def pick_source(value=None, explicit_pid=None):
    if value is None:
        sources = list(Path.cwd().glob("*.cpp"))
        if not sources:
            raise ToolError("no .cpp in this directory")
        source = max(sources, key=lambda p: (p.stat().st_mtime_ns, p.name))
    else:
        source = Path(value if value.endswith(".cpp") else f"{value}.cpp")
    if not source.is_file():
        raise ToolError(f"source file not found: {source}")
    return source.resolve(), problem_id(explicit_pid or source.stem)


def add(args):
    pid = problem_id(args.id) if args.id else pick_source()[1]
    if bool(args.input) != bool(args.output):
        raise ToolError("provide both --input FILE and --output FILE")
    with tempfile.TemporaryDirectory(prefix="cfast-add-") as temp:
        pair = [Path(temp) / "input.txt", Path(temp) / "expected.txt"]
        if args.input:
            pair[0].write_bytes(args.input.read_bytes())
            pair[1].write_bytes(args.output.read_bytes())
        else:
            for path in pair:
                path.touch()
            editor = os.environ.get("EDITOR") or ("subl -w" if shutil.which("subl") else "vi")
            if subprocess.run(shlex.split(editor) + [str(path) for path in pair]).returncode:
                raise ToolError("editor failed; no test saved")
        with problem_lock(pid):
            folder = TESTS / pid / "custom"
            folder.mkdir(parents=True, exist_ok=True)
            indices = [int(p.stem) for p in folder.glob("*.in") if p.stem.isdigit()]
            index = max(indices, default=0) + 1
            for src, suffix in zip(pair, ("in", "out")):
                shutil.copyfile(src, folder / f"{index}.{suffix}")
    print(f"saved custom test {index} for {pid}")
    return 0


def backend():
    """Use oj's pinned CLI engine without its unrelated network update check."""
    python = Path(os.environ.get("CFAST_PYTHON", ROOT / ".venv/bin/python"))
    if not python.is_file():
        raise ToolError("oj environment missing; run the repository's ./install.sh")
    for name in ("g++", "prlimit", "sh", "cat"):
        if shutil.which(name) is None:
            raise ToolError(f"required command missing: {name}; see README prerequisites")
    gnu_time = shutil.which("time")
    if not gnu_time:
        raise ToolError("GNU time is missing; install the 'time' package")
    check = subprocess.run([gnu_time, "--version"], capture_output=True, text=True)
    if check.returncode or "GNU" not in check.stdout:
        raise ToolError("GNU time is required for memory measurement")
    bootstrap = (
        "import logging,sys; from onlinejudge_command.main import get_parser,run_program; "
        "logging.basicConfig(level=logging.INFO); p=get_parser(); "
        "sys.exit(run_program(p.parse_args(),p))"
    )
    return [str(python), "-c", bootstrap], gnu_time


def load_cases(pid, snapshot):
    with problem_lock(pid, exclusive=False):
        folder = TESTS / pid
        if not folder.is_dir():
            raise ToolError(f"no tests saved for {pid} - click Competitive Companion first")
        metadata_path = folder / "meta.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        if not isinstance(metadata, dict):
            raise ToolError(f"invalid metadata for {pid}")
        if metadata.get("interactive"):
            raise ToolError("interactive problems require an interactor; this run mode is unsupported")
        for key, expected in (("input", "stdin"), ("output", "stdout")):
            io = metadata.get(key, {"type": expected})
            if not isinstance(io, dict) or io.get("type") != expected:
                raise ToolError(f"file-based {key} is unsupported; this runner requires {expected}")
        cases = []
        for directory, prefix in ((folder, ""), (folder / "custom", "custom/")):
            paths = sorted(directory.glob("*.in"), key=lambda p: (not p.stem.isdigit(), int(p.stem) if p.stem.isdigit() else p.stem))
            for inp in paths:
                expected = inp.with_suffix(".out")
                if not expected.is_file():
                    raise ToolError(f"missing expected output: {expected}")
                case = snapshot / str(len(cases) + 1)
                case.mkdir()
                shutil.copyfile(inp, case / "case.in")
                shutil.copyfile(expected, case / "case.out")
                cases.append((prefix + inp.stem, case))
        if not cases:
            raise ToolError(f"no tests saved for {pid} - click Competitive Companion first")
    return metadata, cases


def print_section(label, path):
    print(f"--{label}--")
    with path.open("rb") as source:
        raw = source.read(65537)
    print(raw[:65536].decode("utf-8", errors="replace").rstrip("\n"))
    if len(raw) > 65536:
        print("[display truncated after 64 KiB]")


def color(value, ok=False):
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return value
    return f"\033[{32 if ok else 31}m{value}\033[0m"


def check_case(command, gnu_time, executable, case, timeout, memory, eps):
    # Shell redirection keeps runaway output off pipes. prlimit applies to the
    # C++ executable, not Python/oj. GNU time measures this tiny native launcher
    # plus the solution; the Python wrapper's memory is excluded.
    out = case / "actual.txt"
    err = case / "stderr.txt"
    group = case / "group.txt"
    result_file = case / "result.json"
    usage_file = case / "usage.txt"
    limited = shlex.join([
        shutil.which("prlimit"), f"--as={int(memory * 1024 * 1024)}",
        f"--cpu={max(1, math.ceil(timeout))}:{max(1, math.ceil(timeout)) + 1}",
        "--core=0", f"--fsize={OUTPUT_LIMIT}", "--", str(executable),
    ])
    measured = shlex.join([gnu_time, "-f", "%U %S %M", "-o", str(usage_file)]) + " " + limited
    script = (
        f'echo "$PPID" > {shlex.quote(str(group))}; '
        f'{measured} > {shlex.quote(str(out))} 2> {shlex.quote(str(err))}; '
        f'status=$?; cat {shlex.quote(str(out))}; exit "$status"'
    )
    wall_timeout = max(3.0, timeout * 3)
    args = command + [
        "test", "--command", shlex.join(["/bin/sh", "-c", script]),
        "--directory", str(case), "--tle", str(wall_timeout),
        "--mle", str(memory * 1.024), "--gnu-time", gnu_time,
        "--ignore-spaces-and-newlines", "--print-memory", "--log-file", str(result_file),
    ]
    if eps is not None:
        args += ["--error", str(eps)]
    env = dict(os.environ, NO_COLOR="1")
    # actual files use .txt so oj only discovers the expected case.in/case.out.
    try:
        completed = subprocess.run(args, cwd=case, env=env, capture_output=True,
                                   text=True, errors="replace", timeout=wall_timeout + 15)
    except subprocess.TimeoutExpired:
        raise ToolError("oj failed to finish after the testcase timeout; check the backend installation") from None
    finally:
        # oj 11.5.1 sends SIGTERM on timeout. Also reap a solution that ignores
        # SIGTERM; its GNU time process group is recorded before execution.
        if group.exists():
            try:
                pgid = int(group.read_text().strip())
                if pgid > 1 and pgid != os.getpgrp():
                    os.killpg(pgid, signal.SIGKILL)
            except (ValueError, ProcessLookupError):
                pass
    if not result_file.exists():
        raise ToolError("oj backend failed:\n" + (completed.stdout + completed.stderr)[-8000:])
    records = json.loads(result_file.read_text())
    if not isinstance(records, list) or len(records) != 1:
        raise ToolError("oj returned an unexpected testcase report")
    result = records[0]
    # oj 11.5.1's display_result can overwrite RE/TLE with WA when the
    # incomplete output differs. Restore execution verdict precedence from
    # the structured process facts, keeping oj's AC/WA comparison otherwise.
    if result.get("exitcode") is None:
        result["status"] = "TLE"
    elif result["exitcode"] != 0:
        result["status"] = "RE"
    result["wall_elapsed"] = result["elapsed"]
    result["elapsed"] = None
    if usage_file.exists():
        try:
            user, system, rss = usage_file.read_text().splitlines()[-1].split()
            result["elapsed"] = float(user) + float(system)
            result["memory"] = float(rss) / 1000
            if result["elapsed"] > timeout:
                result["status"] = "TLE"
            elif result["memory"] > memory * 1.024:
                result["status"] = "MLE"
        except (ValueError, IndexError):
            if result["status"] != "TLE":
                raise ToolError("GNU time returned invalid resource measurements") from None
    elif result["status"] != "TLE":
        raise ToolError("GNU time did not record resource measurements")
    stderr = err.read_text(encoding="utf-8", errors="replace") if err.exists() else ""
    if "prlimit:" in stderr:
        raise ToolError(f"could not enforce resource limits: {stderr.strip()}")
    # The kernel denies address-space allocations before RSS necessarily grows.
    # Only label an explicit C++ allocation diagnostic as MLE, not every crash.
    if result["status"] == "RE" and ("std::bad_alloc" in stderr or "cannot allocate memory" in stderr.lower()):
        result["status"] = "MLE"
        result["allocation_failure"] = True
    if result["status"] == "RE" and result.get("exitcode") in (128 + signal.SIGXCPU,):
        result["status"] = "TLE"
    if result["status"] == "RE" and (
        result.get("exitcode") == 128 + signal.SIGXFSZ or
        (out.exists() and out.stat().st_size >= OUTPUT_LIMIT) or
        (err.exists() and err.stat().st_size >= OUTPUT_LIMIT)
    ):
        result["status"] = "OLE"
    return result, out, err


def run(args):
    source, pid = pick_source(args.source, args.problem)
    command, gnu_time = backend()
    with tempfile.TemporaryDirectory(prefix=f"cfast-{pid}-") as scratch:
        scratch = Path(scratch)
        metadata, cases = load_cases(pid, scratch)
        timeout = args.timeout or positive(metadata.get("timeLimit", DEFAULT_TIMEOUT * 1000)) / 1000
        memory = args.memory or positive(metadata.get("memoryLimit", DEFAULT_MEMORY))
        if memory < 16:
            raise ToolError("memory limits below 16 MiB are unsupported for this Linux C++ runner")
        print(f"problem {pid}: {source}", flush=True)
        print(f"limits: {timeout:g}s CPU, {memory:g} MiB address space; wall guard {max(3, timeout * 3):g}s", flush=True)
        executable = scratch / "solution"
        print(f"compiling {source.name} ...", flush=True)
        compiled = subprocess.run(["g++", "-std=c++20", "-O2", "-Wall", "-DLOCAL", str(source), "-o", str(executable)])
        if compiled.returncode:
            print(color("compile error"))
            return 1
        passed = 0
        for label, case in cases:
            result, actual, stderr = check_case(command, gnu_time, executable, case, timeout, memory, args.eps)
            status = result["status"]
            elapsed = result["elapsed"]
            memory_used = result.get("memory")
            stats = f"{elapsed:.3f}s CPU" if elapsed is not None else "CPU unavailable"
            stats += f", {result['wall_elapsed']:.3f}s wall"
            if memory_used is not None:
                stats += f", {memory_used / 1.024:.2f} MiB peak RSS"
            if status == "AC":
                passed += 1
                print(f"test {label}: {color('OK', ok=True)} ({stats})", flush=True)
            else:
                verdict = f"RE (exit {result.get('exitcode')})" if status == "RE" else status
                print(f"test {label}: {color(verdict)} ({stats})", flush=True)
                if status == "WA":
                    print_section("input", case / "case.in")
                    print_section("got", actual)
                    print_section("expected", case / "case.out")
                elif status in ("RE", "MLE", "OLE") and stderr.exists() and stderr.stat().st_size:
                    print_section("stderr", stderr)
        print(f"{passed}/{len(cases)} passed")
        return 0 if passed == len(cases) else 1


def parser():
    result = argparse.ArgumentParser(prog="cfast", description=__doc__)
    subs = result.add_subparsers(dest="command")
    listening = subs.add_parser("listen", help="receive Competitive Companion samples")
    listening.add_argument("--port", type=int, default=27121)
    creating = subs.add_parser("new", help="create ID.cpp from your template")
    creating.add_argument("id")
    running = subs.add_parser("run", help="compile and test a C++ file")
    running.add_argument("source", nargs="?")
    running.add_argument("--problem", help="problem ID when the source has another name")
    running.add_argument("--timeout", type=positive, help="per-sample CPU seconds; overrides problem metadata")
    running.add_argument("--memory", type=positive, help="hard address-space ceiling in MiB")
    running.add_argument("--eps", type=positive, help="absolute/relative floating-point tolerance")
    adding = subs.add_parser("add", help="add a custom input/output pair")
    adding.add_argument("id", nargs="?")
    adding.add_argument("--input", type=Path)
    adding.add_argument("--output", type=Path)
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"listen", "new", "run", "add"}
    if not argv or (argv[0] not in commands and argv[0] not in ("-h", "--help")):
        argv.insert(0, "run")
    args = parser().parse_args(argv)
    try:
        if sys.platform != "linux":
            raise ToolError("cfast currently requires Linux for its resource limits")
        if args.command == "listen":
            if not 0 <= args.port <= 65535:
                raise ToolError("port must be between 0 and 65535")
            return listen(args.port)
        if args.command == "new":
            return new(args.id)
        if args.command == "add":
            return add(args)
        return run(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 1
    except (ToolError, OSError, ValueError, argparse.ArgumentTypeError) as error:
        print(f"cfast: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
