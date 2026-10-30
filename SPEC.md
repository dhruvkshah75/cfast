# cfast — effective requirements amendment (2026-10-30)

This amendment applies the user's later explicit instructions and supersedes
conflicting portions of the original specification preserved below.

- The command is `cfast`; the Python entry point remains `cf.py` for the original repository layout.
- Target Linux, home /home/dhruv, repo /home/dhruv/cf-tool; installation must also work under another HOME and clone path.
- The user writes C++ in Sublime Text and invokes one shell command in the solution directory to compile and check all saved cases.
- Use Python and online-judge-tools (`oj`) rather than reimplementing its checker. The old no-pip requirement is superseded. Use Go only if a concrete need arises; it is not required for this scope.
- Time/memory metadata and --timeout/--memory overrides are Phase 1. Include TLE, MLE, RE and compile-error verification. A Linux prlimit address-space ceiling is a hard allocation cap; document that this is conservative and differs from resident-memory accounting on a remote judge. Do not claim identical remote verdicts or hidden-test access.
- Preserve the per-test output and 0/1 exit contract. Show measured memory alongside runtime when available. A confirmed uncaught allocation failure under the cap is MLE; unrelated crashes stay RE. Missing resource tools must be an error, not a silent downgrade.
- Interpret timeLimit/--timeout as CPU seconds, with measured user+system CPU checked after completion and a separate wall guard max(3 seconds, 3 times the CPU limit). Linux CPU termination has whole-second granularity; describe this and the CPU/wall distinction in README.
- Prefer saved problem limits; absent values use clearly printed defaults of 5 seconds and 256 MiB. Run sample blocks unchanged, one process per block. Keep stdout separate from stderr and use token comparison by default. Float tolerance is explicit.
- Save original numbered samples at ~/.cf/tests/<ID>/1.in and 1.out. Preserve user-added cases under custom/ on refresh. Add a small custom-case command in the first version because edge cases are useful for meaningful local checking.
- Interactive and file-I/O problems may be saved, but unsupported run modes must fail clearly. The default template has a case loop whose input count is opt-in.
- Commit significant passing checkpoints. Keep development tests and fixtures ignored and untracked as explicitly requested; keep one-command local unittest verification and record the results in PROGRESS.md.
- No questions for already-known setup details. Ship a reasonable editable template. Keep the GitHub backup private, as specified in the original backup instructions, and document clone/install restore steps.

---

# `cf` — Codeforces Sample Test Runner (Project Spec for a Coding Agent)

> Hand this whole file to the coding agent. It contains the goal, constraints, repo layout, reference implementation, setup steps, acceptance tests, and GitHub backup instructions.

---

## 1. Goal

I am a C++ competitive programmer. During contests I waste time manually copying sample inputs into a file, running my binary, and eyeballing the output. I want a **tiny local CLI called `cf`** that:

1. Gets the sample tests of the Codeforces problem I'm looking at **with one click** (browser extension), saved automatically.
2. Lets me create a new solution file from my template with one command.
3. Compiles my solution and runs it against all saved samples with **one command**, comparing output automatically and showing pass/fail, time, and a diff-style dump on failure.

It must **not solve problems for me**. It only saves time on test handling.

## 2. Hard Requirements

- **Works from any directory.** My solutions live in a deep, topic-wise tree, e.g. `~/algo/Topics/dp/dp-on-strings/1032D.cpp`. I must never need to type or `cd` into a central projects path. I `cd` into the topic folder, run `cf`, done.
- **Tests are stored centrally**, not next to the code: `~/.cf/tests/<PROBLEM_ID>/1.in`, `1.out`, `2.in`, ... (`PROBLEM_ID` = contest id + index, e.g. `1032D`, `1850A`, `1062E`).
- **Test fetching uses Competitive Companion** (browser extension, Chrome/Firefox). It POSTs JSON to `http://127.0.0.1:27121`. Do NOT scrape codeforces.com (Cloudflare blocks it) and do NOT rely on the official API (it has no samples).
- **Single dependency-free Python 3 script** (stdlib only) plus a C++ template. No pip installs.
- **Everything must be reproducible on a new laptop** via a GitHub repo + one `install.sh`.
- Language: C++ only for now (`g++`, `-std=c++20`).

## 3. Commands (CLI contract)

| Command | Behavior |
|---|---|
| `cf listen` | Start HTTP listener on `127.0.0.1:27121`. Runs in a spare terminal tab. On each POST from Competitive Companion, saves tests and prints `saved N tests for <ID> (<name>)`. |
| `cf new <ID>` | Create `<ID>.cpp` in the **current directory** from `template.cpp`. Refuse to overwrite an existing file. |
| `cf` (no args) | Pick the most recently modified `*.cpp` in the current directory, infer `<ID>` from its filename stem, compile, run all tests. |
| `cf <ID>` | Same as above but for `./<ID>.cpp` explicitly. |
| `cf add <ID?>` *(phase 2)* | Open `$EDITOR` to add a custom test pair `N.in`/`N.out` to the problem's test folder. |
| `cf stress <brute.cpp> <gen.py>` *(phase 3)* | Stress test loop; save the failing case as a new test. |

## 4. Run-mode Output Spec

For each test print one line:

- `test 1: OK (0.004s)` in green
- `test 2: WA` in red, followed by sections: `--input--`, `--got--`, `--expected--`
- `test 3: TLE` in red (timeout 5s default, configurable)
- `test 4: RE (exit N)` in red, followed by stderr

Final line: `P/T passed`. Exit code of `cf` = 0 if all passed, 1 otherwise (useful for scripting).

Comparison is **whitespace-token based** (`stdout.split() == expected.split()`), matching Codeforces' default checker. Optional later: floating-point tolerance mode via flag `--eps 1e-6`.

Compile flags: `g++ -std=c++20 -O2 -Wall -DLOCAL`. Compile errors should print the compiler output and exit non-zero without running tests. The binary goes to a temp path (`/tmp/cf_<ID>`), never into the topic directory.

## 5. Competitive Companion Payload (what the listener receives)

POST body is JSON. Fields the listener should use:

```json
{
  "name": "D. Teleporters",
  "group": "Codeforces Round 1062",
  "url": "https://codeforces.com/contest/1062/problem/D",
  "interactive": false,
  "timeLimit": 2000,
  "memoryLimit": 256,
  "tests": [ { "input": "...", "output": "..." } ],
  "testType": "single"
}
```

**Problem ID parsing from `url`** must handle all of these:

- `https://codeforces.com/contest/1032/problem/D` → `1032D`
- `https://codeforces.com/problemset/problem/1032/D` → `1032D`
- `https://codeforces.com/gym/102001/problem/A` → `gym102001A`
- Problems with numeric suffixes like `problem/B1` or `problem/C2` → `1234B1`

If parsing fails, print the URL and skip (do not crash). If `interactive` is true, print a warning that interactive problems are unsupported but still save the samples.

Always respond `200` to the extension, and handle a missing/odd `Content-Length` safely. Bind only to `127.0.0.1`.

## 6. Repository Layout

```
cf-tool/
├── README.md          # short usage + setup (agent should write this from this spec)
├── cf.py              # the CLI (single file, stdlib only)
├── template.cpp       # my C++ boilerplate (agent: ask me to paste mine; ship a sane default)
├── install.sh         # symlinks cf.py into ~/.local/bin/cf, creates ~/.cf/tests
├── .gitignore         # ignore __pycache__/, *.out binaries, .DS_Store
└── SPEC.md            # this file
```

**Important separation:**

- **Versioned in git (the repo):** `cf.py`, `template.cpp`, `install.sh`, docs.
- **NOT versioned:** `~/.cf/tests/` (downloaded samples, regenerable via the extension). Do not commit test data.
- The script must locate its template via `Path(__file__).resolve().parent / "template.cpp"` so it works when invoked through a symlink. Optional override: if `~/.cf/template.cpp` exists, prefer it.

Suggested clone location on disk: `~/dev/cf-tool/` (anywhere is fine, `install.sh` handles paths). This is **separate from my `algo/` practice tree** and must never be inside it.

## 7. Install Script Spec (`install.sh`)

1. `mkdir -p ~/.cf/tests ~/.local/bin`
2. `chmod +x cf.py`
3. `ln -sf "$(pwd)/cf.py" ~/.local/bin/cf`
4. Check `~/.local/bin` is on `PATH`; if not, print the exact `export PATH="$HOME/.local/bin:$PATH"` line to add to `~/.bashrc` / `~/.zshrc` (do not modify rc files silently).
5. Check `g++` and `python3` exist; print a clear error if not.
6. Print next steps: install Competitive Companion, set its custom port to `27121`, run `cf listen`.

Assume Linux or macOS (or WSL). The agent should confirm my OS and adjust if needed (on macOS, default `g++` is clang, which is fine; note `-std=c++20` support).

## 8. Reference Implementation (`cf.py`)

This is a working starting point. The agent should adapt it to the layout above (template path, URL parsing for gym and numeric-suffix indexes, exit codes, `--timeout` flag) and clean it up.

```python
#!/usr/bin/env python3
import sys, re, json, shutil, subprocess, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

HOME = Path.home() / ".cf"
TESTS = HOME / "tests"
TEMPLATE = HOME / "template.cpp"          # TODO: prefer repo-local template.cpp via __file__
CXX = ["g++", "-std=c++20", "-O2", "-Wall", "-DLOCAL"]
PORT = 27121
G, R, X = "\033[32m", "\033[31m", "\033[0m"

def pid_from_url(url):
    m = re.search(r"(?:contest|problemset/problem)/(\d+)/(?:problem/)?(\w+)", url)
    return m.group(1) + m.group(2) if m else None   # TODO: handle gym URLs

# ---------- listen ----------
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        pid = pid_from_url(data.get("url", ""))
        self.send_response(200); self.end_headers()
        if not pid:
            print("could not parse problem id from", data.get("url")); return
        d = TESTS / pid
        shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
        for i, t in enumerate(data["tests"], 1):
            (d / f"{i}.in").write_text(t["input"])
            (d / f"{i}.out").write_text(t["output"])
        print(f"saved {len(data['tests'])} tests for {pid} ({data['name']})")
    def log_message(self, *a): pass

def listen():
    print(f"listening on :{PORT} ...")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

# ---------- new ----------
def new(pid):
    dst = Path.cwd() / f"{pid}.cpp"
    if dst.exists(): print("already exists"); return
    shutil.copy(TEMPLATE, dst)
    print("created", dst)

# ---------- run ----------
def run(pid=None):
    if pid is None:
        cpps = sorted(Path.cwd().glob("*.cpp"), key=lambda p: p.stat().st_mtime)
        if not cpps: sys.exit("no .cpp in this directory")
        src = cpps[-1]; pid = src.stem
    else:
        src = Path.cwd() / f"{pid}.cpp"
    tests = sorted((TESTS / pid).glob("*.in"), key=lambda p: int(p.stem))
    if not tests: sys.exit(f"no tests saved for {pid} - click the extension first")

    exe = Path("/tmp") / f"cf_{pid}"
    print(f"compiling {src.name} ...")
    if subprocess.run(CXX + [str(src), "-o", str(exe)]).returncode:
        sys.exit(f"{R}compile error{X}")

    passed = 0
    for inp in tests:
        exp = inp.with_suffix(".out").read_text()
        t0 = time.time()
        try:
            p = subprocess.run([str(exe)], stdin=inp.open(), capture_output=True,
                               text=True, timeout=5)
        except subprocess.TimeoutExpired:
            print(f"test {inp.stem}: {R}TLE{X}"); continue
        dt = time.time() - t0
        if p.returncode:
            print(f"test {inp.stem}: {R}RE (exit {p.returncode}){X}\n{p.stderr}"); continue
        if p.stdout.split() == exp.split():
            passed += 1
            print(f"test {inp.stem}: {G}OK{X} ({dt:.3f}s)")
        else:
            print(f"test {inp.stem}: {R}WA{X}\n--input--\n{inp.read_text()}"
                  f"--got--\n{p.stdout}--expected--\n{exp}")
    print(f"{passed}/{len(tests)} passed")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["listen"]: listen()
    elif a[:1] == ["new"]: new(a[1])
    else: run(a[0] if a else None)
```

### Known gaps the agent should fix in the reference

- Template path should resolve relative to the repo (`__file__`), not only `~/.cf/`.
- `pid_from_url` does not handle `gym` URLs; verify numeric-suffix indexes (`B1`) work.
- `Content-Length` access can raise `KeyError`; handle gracefully. Wrap JSON parsing in try/except.
- Close the `inp.open()` file handle (use a `with` block).
- Exit with code 1 on any failed test; 0 only if all pass.
- Add `--timeout SECONDS` option and respect `timeLimit` from the payload if saved (store a `meta.json` per problem with name, timeLimit, memoryLimit, url).
- Tests named numerically; `sorted(... key=int)` will crash on non-numeric stems from `cf add`, so use a consistent naming scheme.

## 9. Template (`template.cpp`)

The agent should **ask me to paste my own template** and use it. Until then ship a minimal default with fast IO, a `dbg()` macro gated by `#ifdef LOCAL`, and a `run_case()` / `main()` structure with a multi-test loop. My existing style is C++ with `int64_t`, `INF`, and a debug macro printing `[file:line] (args): values` to `cerr`, like the one in the grandmaster's setup that inspired this.

## 10. Daily Workflow (target experience)

1. Open the problem page in the browser, click the green **+** (Competitive Companion). `cf listen` (in a spare tab) prints `saved 3 tests for 1032D`.
2. `cd ~/algo/Topics/dp/dp-on-strings/`
3. `cf new 1032D`, then edit `1032D.cpp`.
4. `cf` — compiles and runs all samples. Done.

Time from "click" to "results" should be a few seconds, with zero manual copy/paste.

## 11. Acceptance Tests

The agent should verify each of these before declaring done:

1. `cf listen` starts, and a manual `curl -X POST http://127.0.0.1:27121 -d '<sample JSON>'` creates `~/.cf/tests/1032D/1.in` and `1.out`.
2. `cf new 1032D` in an arbitrary nested directory creates the file from the template; running it again does not overwrite.
3. `cf` with a correct solution prints all `OK` and exits 0.
4. A deliberately wrong solution shows `WA` with input / got / expected, and exit code 1.
5. An infinite-loop solution shows `TLE`; a segfault shows `RE`.
6. Compile error stops before running tests and shows the compiler message.
7. A fresh clone + `./install.sh` on a clean machine gives a working `cf` command.
8. Gym and `B1`-style indexes parse correctly (unit-test `pid_from_url`).

## 12. GitHub Backup (so I can recover on a new laptop)

The project is more than one file (script + template + installer), so use a **repo**, not a single gist. (A gist can hold multiple files too, but a repo gives history, a README, and a clean `git clone` + `./install.sh` restore.)

Agent steps:

```bash
cd ~/dev/cf-tool
git init
git add .
git commit -m "Initial commit: cf codeforces sample runner"
# with GitHub CLI:
gh repo create cf-tool --private --source=. --remote=origin --push
# or without gh: create an empty repo on github.com, then
# git remote add origin git@github.com:<username>/cf-tool.git
# git branch -M main && git push -u origin main
```

Notes:

- I am fine with a **private** repo by default; make it public only if I say so.
- Do not commit `~/.cf/tests/` or any compiled binaries.
- Restore on a new laptop: install `g++`, `python3`, `git`; `git clone <repo> ~/dev/cf-tool && cd ~/dev/cf-tool && ./install.sh`; reinstall Competitive Companion and set the port to `27121`.
- Put those restore steps in `README.md`.

## 13. Roadmap (build in this order)

1. **Phase 1 (MVP):** `listen`, `new`, `run`, install script, repo, README. Everything above.
2. **Phase 2:** `cf add` custom tests, `meta.json` with time limits, `--timeout`, `--eps` for float problems.
3. **Phase 3:** `cf stress brute.cpp gen.py` that loops until mismatch and saves the failing case as a new test.
4. **Phase 4:** watch mode (re-run on file save), `-fsanitize=address,undefined` flag (`cf --san`), and an interactor-based mode for interactive problems.

## 14. Non-goals

- No auto-submission to Codeforces, no scraping, no login/cookie handling.
- No solving or hint generation.
- No GUI.

## 15. Questions the agent should ask me before starting

1. Which OS am I on (Linux / macOS / Windows+WSL)?
2. Please paste my existing `template.cpp` (including my `dbg()` macro).
3. Which shell (bash/zsh) so PATH instructions are correct?
4. GitHub username and whether I use SSH or HTTPS for git.
