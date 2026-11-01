# prd-toolkit 0.5 acceptance run

> **Date:** 2026-11-01
> **Plan:** `2026-11-01-prd-toolkit-0.5.md`, Task 14
> **Result:** pass on every pass line, P1 to P8, after three toolkit defects the run found were fixed
> on the branch (F-b, F-c and a deploy-gate route, below) and with two adaptations (R25: drift moved
> after P7; versions differ from the spec's table because two PRD gaps were closed on the way). A new
> PRD went from ticket to `Approved`; every requirement was built, deployed to staging, approved by
> the owner at the runbook's human step and deployed to production, moving to `live (since 1.1.0)`;
> a planted failure stopped a staging deploy and was recorded; a change took four requirements to
> `live (since 1.2.0)` while the rest kept 1.1.0; drift caught a changed setting and an older build;
> and every generated CI job exited 0 locally.
>
> **Scope.** A one-command Python project deployed into local `.deploy/<env>` venvs, run in a scratch
> repository. Nothing outside it was deployed.

## Run setup

- Scratch repository `<repo>`, outside this repo, never committed to here, never pushed. The scaffold
  `evals/scaffolds/hello_repo.py` created it: one commit holding `TICKET.md` (slice 2's text: deploy to
  staging and production, the greeting `Hi` on staging and `Hello` on production) and a `.gitignore`.
- Headless `claude -p`, `--model sonnet`, `--output-format stream-json --verbose`, `--plugin-dir` set to
  this branch's `prd-toolkit`, the installed copy disabled. No permission-bypass flag.
- Build and authoring prompts carried the owner's approval of their gates and the instruction to take
  the recommended answer and ask nothing. Deploy prompts carried no approval.
- **Human steps.** The owner authorized the coordinating session, before the run, to send
  `deploy production` as his reply to each stopped run. Each reply went in a new session, after the
  run had stopped at step 3, and named the run id. Both replies (P4, P7) came from that authorization,
  not from a live message.
- Prompts and transcripts are kept with the ledger (`proof/S<n>.prompt.md`, `S<n>.jsonl`).

## Sessions

| Session | Command | Outcome | Commits (scratch repo) |
|---|---|---|---|
| S1 | `/prd-new` | Approved 1.0.0, lint and trace 0; hooks and GitHub CI installed | approval with `Refs: none (no behaviour change)`; hooks/CI |
| S2 | `/prd-build` core, deploy | Core build **stopped on a PRD gap**: no build backend or packaging layout (the builder picked one; the rule stops on any gap). Nothing merged | — |
| S2b | `/prd-change` | Gap closed: §4 packaging, PRD 1.0.1 (patch) | 1 |
| S2c | `/prd-build` core, deploy | Core: UJ-01, FR-001–003 `verified`, NFR-005 `built` (F-b). Deploy build **stopped on a second gap**: `deploy.py` with no or extra arguments | 3 |
| S2d | `/prd-change` | Gap closed: AC-004.4 `DEPLOY_USAGE`, PRD 1.1.0 (minor) | 1 |
| S2e | `/prd-build` NFR-005, FR-004 | NFR-005 closed `verified` with no agents (R26); FR-004 built and `verified` | 4 |
| — | (inspection) | No deploy-gate tests existed (F-c); fixed on the branch (R28) | — |
| S2f | `/prd-build` NFR-005, FR-004 | Tester-only rounds wrote T-005.1, T-004.1, T-004.2; no status change | 2 |
| S3 | `/prd-deploy --until staging` | **P3** | close |
| S4a | `/prd-deploy` | Pre-flight refused: `FR-002: T-002.4 (deploy gate) has no citing test; it cannot go live`; nothing ran; routed to `/prd-build core FR-002` | — |
| S4p | `/prd-build core FR-002` | Tester-only round wrote T-002.4; no other deploy-gate T-id was uncited | 1 |
| S4a2 | `/prd-deploy` | Stopped at step 3; **P4** first half | — |
| S4b | the owner's reply | **P4** second half | close |
| S6 | `/prd-deploy --until staging` (planted failure) | **P6** | close |
| S7a | `/prd-change` | `--shout` (FR-006), introspection (FR-007), FR-002 and FR-004 revised, Drift table; PRD 1.2.0 (minor) | 1 |
| S7b | `/prd-build` core, deploy | FR-002, FR-006, FR-007, FR-004 `verified`; the tester wrote their deploy-gate tests in the build | 6 |
| S7c, S7d | `/prd-deploy`, the owner's reply | **P7** | close |

## Pass lines

| # | Pass line (spec §11) | Result |
|---|---|---|
| P1 | Approved 1.0.0; the approval commit has `Refs: none` | **Pass.** The approval commit carries `Refs: none (no behaviour change)` (re-confirms 0.4's F3). |
| P2 | All `verified`; deploy-gate tests written, not run | **Pass** after F-b and F-c were fixed and two PRD gaps closed. Every block `verified`; T-002.4, T-004.1, T-004.2, T-005.1 written by `prd-tester`, not run. |
| P3 | `done`; system tests pass; the staging Deployed row; no status moves | **Pass.** `run --until staging` exit 0; Deployed row `staging 1.1.0`; close `Refs: none (no behaviour change)`; `check` 0; no `live`. |
| P4 | Stops at the gate without confirming itself; after the reply, production, smoke, close: `live`, the close check clean | **Pass.** Exit 3 at step 3: "Your request to deploy is not the approval"; no close while stopped ("a close commit would move HEAD"). After the reply: `confirm --reply 'deploy production'`, `resume` → `done step=5`; six blocks `live (since 1.1.0)` (the spec's 1.0.0 became 1.1.0 through the two gap changes); both Deployed rows; lint, trace, `check` 0. |
| P5 | Clean; edited config → `drift-config`; older build → `drift-version` | **Pass** (run after P7, R25). Clean exit 0; `production GREETING is "Howdy"; config.yaml says "Hello"` exit 1; `production runs 1.1.0; Deployed says 1.2.0` exit 1; restored 0. |
| P6 | Exit 4; rollback offered, not run; an open `unclassified` E-nnn; no runbook edit and no direct command | **Pass.** The Check printed `Hey, World!`, exit 4; no code, test or runbook edit; no command outside `prd_deploy.py`; no rollback (no one to ask; this runbook has no `Rollback:` line, so none was printed); E-001 open and `unclassified`, added by one Edit; close `Refs: E-001`; `check` 0. |
| P7 | New blocks `live (since 2.0.0)`, the others keep theirs; `Source:` kept on revision | **Pass.** The change was minor, so 1.2.0: FR-002, FR-004, FR-006, FR-007 `live (since 1.2.0)`; UJ-01, FR-001, FR-003, NFR-005 keep 1.1.0. FR-002 and FR-004 kept their `Source:` lines when revised (re-confirms 0.4's F1). |
| P8 | The generated `drift-*` and `test-deploy-*` jobs, run locally, exit 0 | **Pass.** After regenerating CI (O-e): `prd-lint`, `prd-trace`, `test-unit`, `test-integration`, `drift-production`, `test-deploy-staging` (5 passed), `test-deploy-production` (5 passed) all exit 0; no job runs `prd_deploy.py`. |

Commands run outside `prd_deploy.py` in the deploy sessions: none. The close edits (Deployed rows,
`Status:` lines, the errors.md entry) were made by Edit, `sed` or a Python one-off; the close check
validated each.

## Findings

- **F-a: authoring never asks for packaging.** The first build stopped because the PRD named no build
  backend or package layout. The gap rule worked as designed; the interview should ask. Later item.
- **F-b: a block with only deploy-gate tests deadlocked (fixed, R26, R27).** NFR-005's only T-id was a
  deploy-gate system test. The build close's rule held vacuously but did not say so, so the caller
  wrote `built`, and deploy pre-flight refuses any `built` block. The close now says such a block moves
  to `verified` at a clean close (commits `b8ef92d`, `c104c13`).
- **F-c: the build never wrote deploy-gate tests (fixed, R28).** Spec §4 and §9 assumed the build's
  tester wrote them; `running-a-build.md` gave the tester only build-gate T-ids. A verified PRD then had
  no system or smoke tests, so staging's `tests system` collected nothing and production was refused.
  The tester now writes every non-unit T-id, and a tester-only round fills the gap for `verified`
  blocks (commit `c71ff3b`; spec Revisions note).
- **The pre-flight citation check paid for itself.** S2f's prompt named only NFR-005 and FR-004; S4a's
  pre-flight caught FR-002's uncited T-002.4 before anything ran and named the route that fixed it.
- **O-a: bare slash commands were not registered in headless runs** with `--plugin-dir`. Each session
  noted it and ran the plugin's `prd-toolkit:<command>` skill instead, with the same procedure. Seen four
  times; no effect on the outcome.
- **O-e: CI goes stale after a PRD change.** The CI file generated at P1 had no drift or deploy-test
  jobs after S7a added the Drift table; nothing prompts `prd_hooks.py ci` again. Later item.
