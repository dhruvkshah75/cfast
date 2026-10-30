# cfast implementation progress

The original specification is preserved in SPEC.md. Its amendment records the
user's later requirements: cfast command, Linux, Sublime + terminal, oj backend,
resource checks in the first version, and ignored development tests.

## Checklist

- [x] Initialize /home/dhruv/cf-tool, preserve SPEC.md, add ignore rules and this checklist.
- [x] Phase 1: listener receives Companion JSON on loopback port 27121; saves numbered samples centrally.
- [ ] Acceptance 1: POST realistic JSON to the running listener; verify ~/.cf/tests/1032D/1.in and 1.out.
- [x] Acceptance 8: contest, problemset, gym, B1/C2 URL unit tests.
- [x] Phase 1 / Acceptance 2: template creation from a nested directory; refusal to overwrite; symlink/template resolution.
- [ ] Phase 1 / Acceptance 3: one-command compile and oj run, most recently modified source, OK and exit 0.
- [ ] Acceptance 4: wrong answer prints input/got/expected and exits 1.
- [ ] Acceptance 5: infinite loop TLE and crash RE, nonzero exit.
- [ ] Acceptance 6: compiler errors stop before testing.
- [ ] Discussion: metadata time/memory limits, overrides, hard Linux address-space cap, measured memory, MLE regression.
- [ ] Discussion: custom cases preserved across sample refresh; clear checker/interactive limitations.
- [ ] Phase 1 / Acceptance 7: clean install/reinstall and fresh git clone install; command works from another directory.
- [ ] Phase 1: README documents setup, browser port, Sublime workflow, limits, assumptions, GitHub restore.
- [ ] Run the complete ignored development suite with one command.
- [ ] Fresh final review against SPEC.md; fix gaps; commit everything intended; clean git status.

## Decisions and verification log

- SPEC.md was absent from the workspace. Read cf-tool-SPEC.md in full and copied it to the requested repo as SPEC.md.
- Linux, Python 3.12, g++ 13, GNU time and prlimit are available. Python suffices; Go is unnecessary for this scope.
- The shell sandbox cannot access the systemd user bus. Use portable-to-Linux prlimit address-space limits, document that these differ from cgroup/RSS limits, and verify real allocation failures.
- Development tests live in ignored tests/. They remain on this machine, but are intentionally excluded from git and fresh clones.

## Stuck items

None.

- Checkpoint 1: 8 unittest tests passed (real loopback HTTP, malformed payloads, URL forms, atomic refresh/custom preservation, nested template creation and no-overwrite).
- The shell sandbox denies socket creation; reran the same integration tests with authorized host access and they passed.
- Package verification found that oj 12.0.0 is unreleased. Pinned published 11.5.1; added setuptools 80.9.0 because Python 3.12 removed distutils required by this oj release.
