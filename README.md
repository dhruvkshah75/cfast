# cfast

Write C++ in Sublime Text, save, and run **`cfast 1032D`** in your solution's
directory. cfast compiles once, feeds each saved sample to the executable, and
reports OK, WA, TLE, MLE or RE, resource usage, and mismatched output.

Solutions stay in your existing topic folders. Samples live in `~/.cf/tests/`.
Competitive Companion imports samples; the pinned `online-judge-tools` engine
runs and compares them. No solution generation, scraping, login or submission.

## Install on Linux

On Ubuntu/Debian, install prerequisites if needed:

```bash
sudo apt install python3 python3-venv g++ git time util-linux
git clone <your-repository-url> /home/dhruv/cf-tool
cd /home/dhruv/cf-tool
./install.sh
```

The clone can live anywhere. The installer creates an isolated `.venv/` in the
repo, installs the locked Python dependencies, creates `~/.cf/tests`, and links
`~/.local/bin/cfast` to `cf.py`. Keep the clone: the symlink uses it. Run the
installer again after moving the clone. It can be invoked from another directory.

If the installer prints a PATH instruction, add this to `~/.bashrc` (or
`~/.zshrc`) and open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

The installer never edits shell startup files, replaces an existing regular
`cfast` file, or installs packages into system Python. Internet is needed to
install Python packages initially; imported tests run offline. Python 3.10+,
C++20-capable g++, GNU time, and util-linux `prlimit` are required. No Go compiler
is needed: this scope has no component that benefits from adding Go.

## Browser setup

1. Install [Competitive Companion](https://github.com/jmerle/competitive-companion)
   in Chrome or Firefox.
2. Open its settings and add **27121** to **Custom ports**.
3. Keep this running in a spare terminal:

   ```bash
   cfast listen
   ```

4. Open a Codeforces problem and click the extension's green **+**. The terminal
   prints `saved N tests for 1032D (...)`.

The listener binds only to `127.0.0.1`. It receives sample input/output strings,
the URL, and limits from the extension. It does not fetch hidden judge tests.
If the port is occupied, stop the other listener; alternatively use
`cfast listen --port 27122` and change the extension's custom port to match.

## Daily Sublime + terminal workflow

```bash
cd ~/algo/Topics/dp/dp-on-strings
cfast new 1032D              # optional: create a solution from the template
subl 1032D.cpp               # or open it in your existing Sublime window
# Write and SAVE your solution.
cfast 1032D                  # compile and check every saved case: one command
```

Bare `cfast` selects the most recently modified `*.cpp` in the current directory
and displays its full path. Use an explicit ID when several solutions are open.
The filename stem identifies the samples: `1032D.cpp` uses `1032D/`, and
`gym102001A.cpp` uses `gym102001A/`. Numeric indexes such as `1234B1` work.

```bash
cfast run 1032D.cpp
cfast run main.cpp --problem 1032D
cfast 1032D --timeout 2 --memory 256
cfast 1032D --eps 1e-6       # only when the problem allows this tolerance
```

Compile flags: `g++ -std=c++20 -O2 -Wall -DLOCAL`. Binaries and execution files
live in unique temporary directories and are cleaned up. Nothing is compiled
into your topic folder. Compilation errors stop testing and show g++'s message.

Each complete `.in` file becomes stdin for a fresh process; stdout is compared
with its matching `.out`, ignoring whitespace between tokens. `cerr` remains
separate. Do not use `freopen()` to redirect these streams in your local code.
If a sample contains a leading test count, your C++ code must read it; cfast
does not insert counts, split samples, or infer the input format.

```text
test 1: OK (0.000s CPU, 0.004s wall, 3.12 MiB peak RSS)
test 2: WA (...)
--input--
...
--got--
...
--expected--
...
1/2 passed
```

Successful runs exit 0; failed cases, compile errors and setup errors exit 1.
CLI syntax errors use argparse's exit 2. Colors appear in a terminal; set
`NO_COLOR=1` to disable them. Large failure dumps are visibly truncated at 64 KiB.

## Time and memory checks

`meta.json` stores the imported `timeLimit` in milliseconds and `memoryLimit` in
MiB (the local interpretation of the site's MB label). These limits are active
in the first version. `--timeout` (CPU seconds) and `--memory` (MiB) override them.
Missing metadata uses printed defaults of **5 CPU seconds / 256 MiB**.

- **TLE:** GNU time measures user + system CPU for the native executable chain.
  Linux also applies a CPU rlimit. The kernel limit has whole-second granularity;
  fractional limits are additionally checked against measured CPU on completion.
  GNU time reports CPU in hundredths of a second. A wall-clock guard of
  `max(3 seconds, 3 × CPU limit)` stops sleeping/stalled programs. Both CPU and wall
  time are shown. This separates solution CPU from Ubuntu crash-collector delays.
- **MLE:** Linux `prlimit --as` imposes a hard **virtual address-space** ceiling
  before the C++ program starts. An explicit uncaught `std::bad_alloc`/allocation
  failure under the cap is reported as MLE. Measured peak RSS is also checked.
  An unrelated segmentation fault remains RE. A program that handles malloc
  failure itself may instead exit normally or report RE; an address-space cap
  alone cannot identify every failed allocation. Limits below 16 MiB are rejected.
- **RE:** nonzero exits and fatal signals are reported with the exit status and
  available stderr. Shell-encoded signal exits use `128 + signal`, e.g. 139 for
  SIGSEGV. An allocation diagnostic takes precedence over a generic RE.
- **OLE:** stdout and stderr each have an 8 MiB file cap. Excessive output is
  rejected, rather than filling RAM in a capture pipe. Core files are disabled.

Python/oj's memory is excluded from measurements. A tiny shell, prlimit and GNU
time launcher can contribute a small amount of overhead. Resource tools must be
available; cfast does not silently disable checks. Tests run sequentially.

These are **local checks on available cases**, not a guarantee of a Codeforces
verdict. Virtual address-space accounting is conservative and differs from a
judge's RSS/cgroup accounting. Hardware, compiler, stack policy and checker may
also differ. Programs can stay within small sample limits but exceed limits on
large hidden inputs. Add valid edge cases and maximum-size inputs yourself.
This is a runner for your own single-process C++ programs, not a security sandbox
for hostile code. Cgroup/isolate integration is a possible later backend.

Interactive problems are saved with a warning, but cannot run without an
interactor. File-based I/O is also rejected clearly. Constructive problems with
multiple valid outputs need a problem-specific checker; token comparison cannot
validate alternative valid answers. Float tolerance is opt-in and must match the
problem's rules. System tests, custom checkers, stress testing and watch mode are
not implemented in this version.

## Your template and custom cases

Edit the repo's `template.cpp`, or put your own at `~/.cf/template.cpp` to override
it. The default includes fast I/O, `int64_t`, INF, and a `dbg()` macro writing
`[file:line] (args): values` to stderr under LOCAL. The multi-case loop starts at
one; uncomment `cin >> t` only for problems with a leading case count.
`cfast new` refuses to overwrite existing files.

```bash
cfast add 1032D --input /path/to/input.txt --output /path/to/expected.txt
EDITOR='subl -w' cfast add 1032D
```

The editor command opens an input file and an expected-output file and must wait
until you finish editing. With no ID, `add` uses the latest `.cpp` filename.
Custom pairs live under `~/.cf/tests/1032D/custom/` and run with the samples.
Clicking Companion again replaces only the samples and preserves custom cases.
Samples and custom cases are not automatically backed up to git; copy custom
cases separately if you want to retain them across laptops.

## Repo, verification and restore

```text
cf.py             Python CLI: import, template creation, oj adapter, reporting
template.cpp      editable C++ default
install.sh        isolated dependency install and cfast symlink
requirements.txt  tested dependency versions, including Python 3.12 compatibility
SPEC.md           original spec plus explicit effective-requirements amendment
PROGRESS.md       acceptance checklist, decisions and verification evidence
```

Assumptions: Linux, Python 3.10+, bash/zsh PATH instructions, one-process C++, an
editable default template because none was supplied, and Python throughout
because Go adds no necessary capability here. `CFAST_HOME` may override `~/.cf`
for isolated data; `CFAST_PYTHON` may point to another compatible oj environment.
The adapter uses the pinned oj CLI engine and suppresses its network update
check, so running saved samples needs no network connection.

Per the owner's request, development tests/fixtures are in ignored `tests/` and
are **not shipped in git**. On the development checkout, run the whole suite:

```bash
cd /home/dhruv/cf-tool
python3 -m unittest discover -s tests -v
```

The suite compiles real C++, starts a real loopback listener, and verifies clean
installs. Install tests use cached wheels if present, otherwise need network.
The local suite will not be present in a fresh clone; verification results are
recorded in PROGRESS.md.

Create a **private** GitHub repository for backup, then add its remote and push:

```bash
git remote add origin <your-private-repository-url>
git push -u origin main
```

On a new Linux laptop, install the prerequisites above, clone your repository,
run `./install.sh`, set PATH if needed, reinstall Competitive Companion, add port
27121, and run `cfast listen`. Re-import samples from the browser. Your solution
tree can live anywhere; back it up separately. The installer and restore steps
do not depend on the original `/home/dhruv` path.
