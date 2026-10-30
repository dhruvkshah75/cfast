# cfast

**Run Codeforces samples from your terminal with one command.**

Write C++ in your preferred editor, save your file, and run `cfast 1032D`.
cfast compiles your solution, runs every saved sample, and reports the verdict,
CPU time, wall time, and peak memory usage.

- Import samples with one click using Competitive Companion.
- Keep solutions in your existing folders and samples in `~/.cf/tests/`.
- Check outputs with [online-judge-tools](https://github.com/online-judge-tools/oj).
- Apply local CPU and memory limits, with readable output on failure.
- Save custom cases and keep them when refreshing samples.

## Installation

Requires Linux, Python 3.10+, a C++20-capable `g++`, GNU `time`, and `prlimit`.
On Ubuntu or Debian:

```bash
sudo apt install python3 python3-venv g++ git time util-linux
```

Clone the repository outside your solutions folder and install:

```bash
mkdir -p ~/dev
git clone https://github.com/dhruvkshah75/cfast.git ~/dev/cfast
cd ~/dev/cfast
./install.sh
```

The installer creates an isolated Python environment in `.venv/` and links
`~/.local/bin/cfast` to the checkout. Keep the checkout in place; rerun the
installer if you move it. Installation needs internet access; testing saved
cases works offline.

If `~/.local/bin` is not on your PATH, add this to `~/.bashrc` or `~/.zshrc`
and open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Import samples

1. Install [Competitive Companion](https://github.com/jmerle/competitive-companion)
   in Chrome or Firefox.
2. Add **27121** to the extension's **Custom ports** setting.
3. Start the listener in a spare terminal:

   ```bash
   cfast listen
   ```

4. Open a Codeforces problem and click the extension's green **+**.
   The listener confirms how many samples were saved.

The listener accepts connections only on `127.0.0.1`. It receives the problem's
samples and resource limits from the extension. For another port, use
`cfast listen --port 27122` and update the extension setting to match.

## Write, save, test

From any solution directory:

```bash
cfast new 1032D       # Create 1032D.cpp from your template
subl 1032D.cpp        # Or open it in another editor
# Write and save your solution.
cfast 1032D          # Compile and run all saved cases
```

Bare `cfast` selects the most recently modified `*.cpp` in the current directory
and prints the selected path. Use an explicit ID when working on several files.
The filename identifies the problem: `1032D.cpp`, `1234B1.cpp`, or
`gym102001A.cpp`.

| Command | Purpose |
| --- | --- |
| `cfast listen` | Receive samples from Competitive Companion |
| `cfast new 1032D` | Create a solution file; refuse to overwrite it |
| `cfast` | Compile and test the latest C++ file in this directory |
| `cfast 1032D` | Compile and test `1032D.cpp` |
| `cfast run main.cpp --problem 1032D` | Associate a differently named file with saved samples |
| `cfast add 1032D` | Open an editor to add a custom case |

### Results

```text
test 1: OK (0.000s CPU, 0.004s wall, 3.12 MiB peak RSS)
test 2: WA (...)
--input--
2 3
--got--
6
--expected--
5
1/2 passed
```

Verdicts include **OK**, **WA**, **TLE**, **MLE**, **RE**, and **OLE**.
Compilation errors stop the run and show the compiler output. Successful runs
exit with status `0`; failed tests and setup errors exit with `1`. Invalid CLI
syntax exits with `2`.

Each complete sample is passed to a fresh process through standard input.
Standard output is compared as whitespace-separated tokens; `cerr` stays separate.
Your solution must handle its own input format, including any leading test count.
Use standard input/output rather than `freopen()` redirects.

Compilation uses `g++ -std=c++20 -O2 -Wall -DLOCAL`. Binaries and execution files
are created in temporary directories and cleaned up after the run.

## Limits and comparison

Problem limits are imported automatically. If metadata is missing, cfast uses
**5 CPU seconds** and **256 MiB**. Override them when needed:

```bash
cfast 1032D --timeout 2 --memory 256
cfast 1032D --eps 1e-6       # Explicit absolute/relative floating-point tolerance
```

- **Time:** the primary limit is user + system CPU time. Linux CPU limits have
  whole-second granularity; fractional limits are also checked after execution.
  A separate wall-clock guard of `max(3 seconds, 3 × CPU limit)` stops stalled
  programs. GNU time reports CPU usage in hundredths of a second.
- **Memory:** `prlimit` enforces a hard **virtual address-space** ceiling, and peak
  resident memory is measured separately. An explicit uncaught allocation failure
  under the cap is reported as MLE. A program that handles allocation failure
  itself may instead exit normally or report RE. Limits below 16 MiB are unsupported.
- **Output:** standard output and standard error each have an 8 MiB file limit.
  Failure displays are truncated at 64 KiB. Set `NO_COLOR=1` to disable colors.

Local results apply to the cases you run. They cannot guarantee a Codeforces
verdict: hidden tests, hardware, compiler settings, and memory accounting differ.
The virtual-memory cap can be stricter than a judge's resident-memory limit.
The Python wrapper's memory is excluded; native launchers add a small overhead.
Add boundary cases and large valid inputs to check more than the samples.

Interactive problems and file-based I/O are unsupported. Problems with multiple
valid outputs need a problem-specific checker; token comparison cannot validate
alternative answers. Floating-point tolerance must match the problem's rules.
cfast is intended for your own single-process C++ programs, not as a security
sandbox for untrusted executables.

## Templates and custom cases

Edit `template.cpp`, or put a personal override at `~/.cf/template.cpp`.
The template's test-count input is opt-in: uncomment `cin >> t` only when the
problem starts with a test count.

Add an input/expected-output pair from files:

```bash
cfast add 1032D --input input.txt --output expected.txt
```

Or open both files in an editor that waits until editing is finished:

```bash
EDITOR='subl -w' cfast add 1032D
```

Custom cases are stored under `~/.cf/tests/1032D/custom/` and run with the samples.
Importing the problem again refreshes the samples and preserves custom cases.
With no ID, `cfast add` uses the latest C++ file's name.

## Moving to another machine

Repeat the installation and browser setup on the new Linux machine. Samples can
be imported again. Back up your solution folders and custom cases separately;
they are not stored in this repository.
