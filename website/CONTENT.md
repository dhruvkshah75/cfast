# Product facts for the landing page

Source: the repository README, `cf.py`, and `install.sh`. This document separates
the CLI's actual behavior from illustrative website demonstrations.

## What visitors need to understand

cfast imports Codeforces samples through Competitive Companion, compiles C++20
solutions, and runs all saved cases with one shell command from the user's
solution directory. It supports a workflow with Sublime Text or any other editor.

The page's primary conversion is reaching the installation instructions.
The visual proof is an explicitly illustrative terminal demonstration, backed
by links to the source and documentation rather than invented social proof.

## Important details, in order

1. Run `cfast <ID>` to compile and check saved cases. Bare `cfast` chooses the
   most recently modified C++ file in the current directory.
2. Run `cfast listen`, set Companion's custom port to 27121, and click its plus
   button on a Codeforces problem to import samples and limits.
3. Solutions stay in the user's folders. Downloaded samples and custom cases
   live under `~/.cf/tests/<ID>/`. Temporary execution files are removed.
4. Results include output comparison, CPU time, wall time, peak RSS, and verdicts
   OK, WA, TLE, MLE, RE, and OLE. Compilation failures stop before testing.
5. Got and expected are plain white terminal text, on both passes and failures.
   Debug output stays separate from stdout; locations use filename and line.
6. Imported problem limits can be overridden. The Linux memory cap applies to
   address space, not just RSS, and can be stricter than the remote judge.
   CPU enforcement has whole-second granularity and a separate wall guard.
7. Custom cases survive imports. Cleanup previews by default. A full reset also
   removes custom cases; sample-only cleanup preserves them.
8. The local tool requires Linux, Python 3.10+, C++20 g++, GNU time, prlimit,
   Git, and network access during installation. Saved-case runs work offline.
9. Interactive problems, file I/O, and special checkers are unsupported.
   Local samples do not represent hidden tests or guarantee acceptance.
10. Source, installation instructions, issue reporting, and restoration guidance
    are available in the GitHub repository.

## Page outline

Hero and verdict demo → compatibility → workflow benefits and real C++ example
→ animated benefit statement → three-step daily workflow → installation and
Companion setup → command reference → six practical FAQs → final install action.

The layout is a classic product demonstration with editorial sections. It uses
a warm light canvas for reading, dark terminal surfaces for product output,
orange actions, and one primary CTA: “Install cfast”. Geist is the body and
display typeface; Geist Mono is reserved for code and numeric output.

## Motion and accessibility

Terminal lines enter in reading order when explicitly replayed. Sections reveal
once, with a separate word-by-word benefit statement. Mobile navigation uses a
full-height panel, keyboard focus management, and an Escape action. Both tab
groups support arrow keys and Home/End. Reduced motion removes movement and
reveals the statement immediately. The default HTML remains readable without JS.

## Search

Evergreen, indexable product page. Title: “cfast — Codeforces samples, one
terminal command”. The description names the platform, language, import flow,
and output/resource checking. There are no unverified ratings or search schema
claims. Legal and missing-page documents are not indexed.
