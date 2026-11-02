# prd-toolkit 0.6 acceptance run

> **Date:** 2026-11-01
> **Spec:** `2026-11-01-prd-toolkit-0.6-design.md`, §13
> **Result:** **pass on every pass line, Q0 to Q6**, on the third attempt. The run resumed in place
> after F-4 was fixed. Four toolkit defects found on the way (F-1 to F-4) were fixed on the branch.
> - **Q1.** A bug that no test caught was reported, reproduced, proposed as `code bug` with the ACs
>   quoted, and confirmed. A patch added a new system T-id `known-failing: E-001`. Its strict
>   expected failure was the red proof, and CI stayed green. The `--fixes` build removed the marker,
>   the deploy's system tests passed it, and FR-002 went `live (since 1.0.1)`. E-001 was resolved
>   with `check` 0.
> - **Q2.** A spec gap went through a minor 1.1.0 change, build and deploy to
>   `live (since 1.1.0)`.
> - **Q3.** A killed step: `resume` refused, `recover` ran on the owner's words, then `rollback`,
>   and an entry was added with `check` 0.
> - **Q4.** A report the PRD answers on purpose was resolved `not a defect`, with only `errors.md`
>   changed.
> - **Q5.** The page is self-contained with both tabs, makes no request in a browser, and was
>   published as a private Artifact. The renderer refused a summary that cited another area's ID.
> - **Q6.** A change added a build-gate level. Its committed tree failed the `prd-lint` job's
>   `check --ci` with `stale:` until the change's own close re-ran `ci`.
>
> **Scope.** The `greet` scaffold, deployed into local `.deploy/<env>` installs in a scratch
> repository. Nothing outside it was deployed.

**Earlier attempts.**
- **Attempt 1** (`STOPPED.md`, S0a–S1f) stopped at Q1's deploy. Three findings, all fixed on the
  branch (8c29514, 71dc403):
  - F-1: the scaffold's T-002.2 pinned `1.0.0`.
  - F-2 (R16): no error class fit a test case that contradicts its AC.
  - O-1 (R17): `propose` could not set `Touches:`.
- **Attempt 2** (`STOPPED-2.md`, T0a–T1b) stopped at Q1's patch on F-3: the ledger text turned
  `prd_lint` red. Fixed in bfb6fd0 (R19).
- **Attempt 3** (`STOPPED-3.md`, V0a–V1c) stopped at the `--fixes` close on F-4: a deploy-gate
  regression T-id deadlocked the build close. Fixed in 2f43350 and e014fb3 (R21). The proof resumed
  in place in the same repository (V1d onward).
- All three repositories and their transcripts are kept.

## Run setup

- **Scratch repository** `<repo>`: outside this repo, never pushed, no remote (R13). Built with
  `deploy_repo.py <repo> ready` from the branch scaffold, then the managed CLAUDE.md block written
  and committed exactly as `error_repo.py` does, then `prd_hooks.py ci --github docs/prd/greet`
  (vendored), committed with `Refs: none`. Jobs: `prd-lint` (lint `--ci`, `prd_hooks.py check
  --ci`), `prd-trace`, `test-unit`, `drift-production`, `test-deploy-staging`,
  `test-deploy-production`.
- **Sessions:** headless `claude -p`, `--model sonnet`, `--output-format stream-json --verbose`,
  `--plugin-dir` set to this branch's `prd-toolkit`, the installed copy disabled, tools allowed by
  name, no permission-bypass flag. One session ran at a time.
- **Owner's replies.** Sent under spec §13's authorization (R14), each in a new session after the
  stop it answers, naming the run or entry:
  - `deploy production`, four times;
  - `yes, it's a code bug` (E-001) and `yes, it's a spec gap` (E-002);
  - `approved`, twice, each for a change on its entry's route;
  - Q3's recover words;
  - Q4's verdict;
  - `approved` for Q6's change, under R22.

  No other reply was sent.
- **The Q1 bug (R18).** An ordinary code commit, dd5e8f4, makes the launcher run
  `exec python3 -m greet $@`, unquoted. An installed `greet "Ana Maria"` then prints
  `usage: greet <name>`.
  - No existing T-id catches it: the unit tests call `main` directly, and T-002.1 and both runbook
    Checks use the one-word `World`.
  - It went to staging undetected (V1pre).
- **The Q3 killed state.** As in `error_repo.py`'s `killed-step`: a real `run --until staging`,
  with its log cut back to the header and one unfinished `start` on step 1. Adaptation: only
  `.deploy/staging*` was restored from a snapshot taken before the run, because this repository has
  a live production install.
- **Files:** `proof/V<n>.prompt.md`, `.jsonl`, `.stderr` (earlier attempts `S<n>`, `T<n>`); the
  running log is `proof/notes.md`; the page is `proof/greet-prd-1.1.0.html`.

## Sessions

| Session | Command | Outcome | Commits (scratch repo) |
|---|---|---|---|
| V0a, V0b | `/prd-deploy`, the reply | **Q0**: stop at step 3; then done, FR-001, FR-002 `live (since 1.0.0)` | close |
| — | (driver) | The launcher bug, as an ordinary code commit | 1 |
| V1pre | `/prd-deploy --until staging` | done; the bug passed the Check and T-002.1 | close |
| V1a, V1b | `/prd-error <report>`, the reply | E-001 `code bug` proposed and confirmed; patch drafted | record, propose, confirm |
| V1c | the owner's `approved` | approval; red round (strict xfail); `--fixes` build stopped on F-4 | approval, red test, fix, un-mark, close |
| V1d | `/prd-build greet FR-002 --fixes E-001` | (after R21) marker line removed; FR-002 `verified`; trace 0 | close |
| V1e, V1f | `/prd-deploy`, the reply | system tests `2 passed` incl. T-002.3; FR-002 `live (since 1.0.1)` | close |
| V1g | `/prd-error E-001` | resolved `T-002.3 [system], PRD 1.0.1, fixed in e2d5935`; check 0 | resolve |
| V2a, V2b | `/prd-error <report>`, the reply | E-002 `spec gap` (sections searched); confirmed; 1.1.0 drafted | record, propose, confirm |
| V2c | the owner's `approved` | approval; `--fixes` build (unit tests first); resolved; check 0 | approval, code, close, resolve |
| V2d, V2e | `/prd-deploy`, the reply | FR-001 `live (since 1.1.0)` | close |
| V3a | `/prd-deploy <run>` "carry on" | `resume` refused: "step 1 started and did not finish" | — |
| V3b | the owner's recover words | `recover` → failed; `rollback` pass; E-003 added; check 0 | close |
| V4a, V4b | `/prd-error <report>`, the verdict | E-004 resolved `not a defect`; check 0 | record, propose, confirm, resolve |
| V5a | `/prd-publish` | page and summaries written, untracked; render exit 0 | — |
| V6a | `/prd-change` (level + T-id) | dry run failed on 3 real gaps: my prompt; draft discarded | — |
| V6b | `/prd-change` (rerun) | 1.2.0 drafted, dry run clean; stopped for approval | — |
| V6c | the owner's `approved` (R22) | **Q6**: Approved 1.2.0; the close re-ran `ci --github --force` itself | approval, CI |

## Pass lines

| # | Pass line (spec §13) | Result |
|---|---|---|
| Q0 | (start, R13) the scaffold taken to `live` | **Pass.** Exit 3 at step 3 with no self-confirm. After the reply: `confirm --reply 'deploy production'`, `resume` → done, both Deployed rows, both blocks `live (since 1.0.0)`. Lint, trace and `prd_deploy.py check` 0. |
| Q1 | Reproduced; `code bug` proposed with a quote; confirmed; a patch adds a known-failing T-id; its test fails as expected and every CI job exits 0; `--fixes` build: tag gone, test passes; deploy `live`; `check` 0 | **Pass, after F-4/R21.** Reproduced with one run of the staging launcher. Proposed `code bug` quoting AC-001.2 and AC-002.1, `Touches: FR-001, FR-002`; confirmed `yes, it's a code bug`. The patch added T-002.3 [system] `known-failing: E-001`. The test was `@pytest.mark.xfail(strict=True)` with the citation `@prd T-002.3 known-failing E-001`, and RESULTS gave `T-002.3: known-failing E-001`. CI at 4a6b492: prd-lint 0, prd-trace 0, test-unit 0, drift-production 0, test-deploy-staging 0 (`1 passed, 1 xfailed`); test-deploy-production 1 (O-4, deferred). After the fix: marker and tag gone, the case line removed at the clean close (R21), FR-002 `verified`, trace 0. The deploy's step 2 gave `test_two_word_name.py .`, `2 passed`, and FR-002 went `live (since 1.0.1)`. Resolved; `check 1b33220..HEAD` 0. |
| Q2 | Spec gap: proposed with the sections searched; confirmed; minor change, build, deploy; the new blocks `live` | **Pass.** `greet ""` printed `Hi, !`. The proposal was `spec gap`, naming the sections searched (features/greet.md, test-cases/greet.yaml, testing.md, prd.md); confirmed. The minor 1.1.0 change added AC-001.3, `GREET_NAME_BLANK`, T-001.3 and T-001.4 [unit]. The `--fixes` build wrote tests first; resolved `T-001.3 [unit], PRD 1.1.0, fixed in c9448a0`. The deploy took FR-001 `live (since 1.1.0)`, and production `greet ""` now gives `usage: greet <name>`, exit 2. `check b649546..HEAD` 0. |
| Q3 | Killed step: `resume` refuses; `recover` → failed; `rollback` runs; entry added; `check` 0 | **Pass.** `resume` refused ("step 1 started and did not finish"). After the owner's words, `recover` wrote `recover` and a step `fail` "recovered: no result after start" (exit 4). `rollback --step 1` passed; E-003 was added by `prd_error.py new`; the close touched only errors.md; `prd_deploy.py check` 0. |
| Q4 | Not a defect: confirmed `not a defect`; no change outside errors.md | **Pass.** The report wanted a full stop; the PRD says `!` (AC-001.1, AC-001.2). The reply, "That's not a defect: the PRD says the greeting ends with '!'", was confirmed verbatim and resolved `not a defect:` quoting AC-001.2. `git diff --stat 5c206e9..HEAD` shows errors.md only; `check` 0. |
| Q5 | `/prd-publish`: both tabs; no network; a summary citing another area's ID refused; an Artifact | **Pass.** The page is 17,081 bytes. It has zero `<script`, `<link`, `<img`, `<iframe`, `src=`, `@import`, `url(` and `http(s)://`; CSS-only `Business`/`Technical` tabs; light and dark; no `Evidence:`. Refusals, exit 1 with no page written: `greet: FR-003 belongs to area 'farewell'` (on a throwaway two-area copy), `area 'billing' does not exist`, `greet: FR-009 is not defined`. Opened in a browser over a local server: the `Business` and `Technical` tabs render and switch, and the only network request is the page itself. The same file was published, unchanged, as a private Artifact. |
| Q6 | A change adding a level: the `prd-lint` job fails `stale` until `ci` is re-run | **Pass.** The 1.2.0 change (build-gate `integration` level, T-001.5 under AC-001.3) was approved and committed at 6e68683. The `prd-lint` job's commands run on that tree, before any `ci` re-run: `prd_lint.py --ci` 0, then `prd_hooks.py check --ci` printed `stale: .github/workflows/prd-toolkit.yml: re-run prd_hooks.py ci --github --force` and exited **1**. The close then ran `prd_hooks.py ci --github --force` itself and committed it (6c9d60c, adding a `test-integration` job). At 6c9d60c, lint `--ci` 0 and `check --ci` **0**. A driver re-run of `ci --github --force` changed nothing. |

## Findings

| ID | Finding | Disposition |
|---|---|---|
| F-1 | The scaffold's T-002.2 and its smoke test pinned the version `1.0.0`, so every version bump failed production smoke (attempt 1). | Fixed on the branch (8c29514). |
| F-2 | No error class covered a test case or contract that contradicts its own AC (attempt 1). | Fixed, R16 (8c29514, 71dc403). |
| F-3 | The ledger text the error loop wrote (a quoted `<name>`) turned `prd_lint` red, with no way out (attempt 2). | Fixed, R19 (bfb6fd0). |
| F-4 | A deploy-gate regression T-id deadlocked the `--fixes` close (attempt 3). | Fixed, R21 (2f43350, e014fb3). |
| O-1 | An entry recorded before diagnosis could never gain `Touches:`. | Fixed, R17; held in V1a. |
| O-2 | The first scaffold bug was caught by an existing unit T-id, so the known-failing path never ran. | Resolved by R18; exercised in Q1. |
| O-3 | Minor procedure drift in sessions: chained commits, pipes to `tail`, a tester round as `Mode: suite` where `Mode: write` was written. | None; no effect on any outcome. |
| O-4 | `test-deploy-production` fails between a version bump and its deploy: T-002.2 compares production with the current `prd.md`, though AC-002.2 says "the version the install was made from". | Deferred minor. |
| O-5 | The approval commit of a change made for an entry carried `Refs: none` (20f538f); step 5 says it cites the entry. | Deferred minor. |
| O-6 | A rollback after `recover` of a step that "left nothing installed" restored the install before the last one: staging runs 1.0.1 while its Deployed row says 1.1.0. | Deferred minor. |
| O-7 | Q4's proposal was `invalid requirement` instead of the claimed class with a `not a defect:` diagnosis; the entry keeps that class beside a `not a defect` resolution. | Deferred minor. |
| O-8 | V6b said "there are no generated CI include files" although `.github/workflows/prd-toolkit.yml` exists. | Disproven by Q6: V6c's close looked for both paths and regenerated and committed the file itself. The claim came from a session whose close had not run. |

**What held.**
- No request was taken as a confirmation, approval or production reply in any attempt, and every
  proposal waited for its reply.
- The failure, recover and rollback paths followed the deploy procedure exactly.
- Sessions stopped on real PRD gaps instead of reading code (V6a, and attempt 3's V1c).
- Every entry closed with `prd_error.py check` 0, and every deploy close with `prd_deploy.py check`
  0.

**Left as found.**
- The new `test-integration` job exits 4 (no tests ran) until `/prd-build greet FR-001` writes
  T-001.5's test. FR-001 is `approved`, the expected state between a change and its build; the
  proof did not build it.
- E-003 (Q3's failed run) stays open and `unclassified`.
- The work sits on `prd-build/greet-FR-002`, never merged to the default branch, as the build
  procedure says.
