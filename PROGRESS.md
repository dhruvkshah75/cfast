# cfast implementation progress

The original specification is preserved in SPEC.md. Its amendment records the
user's later requirements: cfast command, Linux, Sublime + terminal, oj backend,
resource checks in the first version, and ignored development tests.

## Checklist

- [x] Initialize /home/dhruv/cf-tool, preserve SPEC.md, add ignore rules and this checklist.
- [x] Phase 1: listener receives Companion JSON on loopback port 27121; saves numbered samples centrally.
- [x] Acceptance 1: POST realistic JSON to the running listener; verify ~/.cf/tests/1032D/1.in and 1.out.
- [x] Acceptance 8: contest, problemset, gym, B1/C2 URL unit tests.
- [x] Phase 1 / Acceptance 2: template creation from a nested directory; refusal to overwrite; symlink/template resolution.
- [x] Phase 1 / Acceptance 3: one-command compile and oj run, most recently modified source, OK and exit 0.
- [x] Acceptance 4: wrong answer prints input/got/expected and exits 1.
- [x] Acceptance 5: infinite loop TLE and crash RE, nonzero exit.
- [x] Acceptance 6: compiler errors stop before testing.
- [x] Discussion: metadata time/memory limits, overrides, hard Linux address-space cap, measured memory, MLE regression.
- [x] Discussion: custom cases preserved across sample refresh; clear checker/interactive limitations.
- [x] Phase 1 / Acceptance 7: clean install/reinstall and fresh git clone install; command works from another directory.
- [x] Phase 1: README documents setup, browser port, Sublime workflow, limits, assumptions, GitHub restore.
- [x] Run the complete ignored development suite with one command.
- [x] Fresh final review against SPEC.md; fix gaps; commit everything intended; clean git status.

## Decisions and verification log

- SPEC.md was absent from the workspace. Read cf-tool-SPEC.md in full and copied it to the requested repo as SPEC.md.
- Linux, Python 3.12, g++ 13, GNU time and prlimit are available. Python suffices; Go is unnecessary for this scope.
- The shell sandbox cannot access the systemd user bus. Use portable-to-Linux prlimit address-space limits, document that these differ from cgroup/RSS limits, and verify real allocation failures.
- Development tests live in ignored tests/. They remain on this machine, but are intentionally excluded from git and fresh clones.

- Checkpoint 1: 8 unittest tests passed (real loopback HTTP, malformed payloads, URL forms, atomic refresh/custom preservation, nested template creation and no-overwrite).
- The shell sandbox denies socket creation; reran the same integration tests with authorized host access and they passed.
- Package verification found that oj 12.0.0 is unreleased. Pinned published 11.5.1; added setuptools 80.9.0 because Python 3.12 removed distutils required by this oj release.

- Checkpoint 2: 19 unittest tests passed in 12.03s against installed oj 11.5.1 and real g++ binaries: OK, WA, TLE, RE, compile errors, 128 MiB allocation rejected at 64 MiB and accepted at 256 MiB, metadata timing, custom cases and unsupported interactive mode.
- Crash verification exposed Ubuntu apport core-collection delay. Use measured CPU time as the primary limit, Linux CPU allocation limits, and an independent wall guard max(3s, 3 * CPU limit). This avoids charging crash collection to the solution. Subsecond CPU limits are checked after completion; kernel CPU termination is rounded up to whole seconds.
- Record GNU time measurements for the native launcher/solution only; cap file output at 8 MiB and kill the testcase process group even if a program ignores SIGTERM.
- Lock all tested Python dependency versions for reproducible installs.

- Checkpoint 3: 27 local unittest tests passed in 24.90s, including clean install/reinstall from a path with spaces, shell use from another directory, template resolution through the symlink, float tolerance, output limiting, and SIGTERM-ignoring process cleanup.
- Expanded tests found an upstream oj 11.5.1 bug: an output mismatch overwrites RE/TLE with WA. Normalize verdict precedence from oj process facts; added nonempty-expected-output crash/TLE/MLE regressions and an explicit exit-7 regression.
- README and executable installer completed; fresh git-clone and real-home smoke verification remain.

## Final review and acceptance evidence

- Final full local suite: `python3 -m unittest discover -s tests -v` — 28 tests passed in 29.924s, including a real fresh `git clone` into a path with spaces, isolated HOME, no preexisting venv, and successful installation/run. Development tests did not appear in the clone.
- `python3 tests/smoke_real_home.py` passed against the actual installed `/home/dhruv/.local/bin/cfast`. Removed that symlink, reinstalled from `/tmp`, started `cfast listen` on 127.0.0.1:27121, POSTed realistic Companion JSON with Python urllib, and verified actual `/home/dhruv/.cf/tests/1032D/1.in` and `1.out` contents.
- The installed command created a template in a nested directory, refused overwrite, and produced OK/exit 0, WA/exit 1, TLE/exit 1, RE/exit 1, MLE/exit 1, and compile error/exit 1 for six real C++ fixtures. Fixture samples were removed (or prior samples restored) afterward, and the listener was stopped.
- Reviewed all repo files against the full original SPEC plus the effective amendment. Original layout retained; command renamed cfast; later oj/resource requirements implemented and documented; no unnecessary Go component; known local-versus-remote limits stated explicitly.
- `sh -n install.sh`, Python byte-compilation, and `git diff --check` passed. Git tracks only .gitignore, cf.py, template.cpp, install.sh, requirements.txt, README.md, SPEC.md, and PROGRESS.md. Tests, wheels, runtime data, venv and binaries are excluded.
- Private GitHub backup: https://github.com/dhruvkshah75/cf-tool. Final commit is pushed on main; remote HEAD and local HEAD are checked for equality after push.
- All requested checkpoints are complete. Final commit records this review; final status verification must be empty (ignored local test files intentionally remain).

## Stuck items

None. No failure reached five unsuccessful fixes. Environment/dependency issues and both resource/verdict bugs were diagnosed and resolved with passing regressions.
