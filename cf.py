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
import socket
import subprocess
import sys
import tempfile
import threading
import uuid
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
    running.add_argument("--timeout", type=positive, help="per-sample seconds; overrides problem metadata")
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
    except (ToolError, OSError, ValueError) as error:
        print(f"cfast: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
