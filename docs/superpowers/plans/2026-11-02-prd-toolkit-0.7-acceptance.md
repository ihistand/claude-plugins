# prd-toolkit 0.7 acceptance run

> **Date:** 2026-11-02
> **Spec:** `2026-11-02-prd-toolkit-0.7-design.md`, §13 (Q1 to Q6), with §6 (its **Sessions** paragraph) and the
> Revisions block (R-13a added by this run)
> **Result:** **pass on every pass line, Q1 to Q6**, on the third attempt. The proof resumed in place after F-3
> was fixed. Three toolkit defects found on the way (F-1 to F-3) were fixed on the branch.
> - **Q1.** `add` wrote both sides, `sync` copied only the `greet` key, and lint and `check` exit 0 in both
>   repositories, after the upstream's Consumers row went through its own `/prd-change` in greet (R-2).
> - **Q2.** `impact` named the client. CS-001 was written, and both PRDs were edited and approved by one reply.
>   greet was built and deployed to staging. The client was synced and built. The client's first build stopped on
>   a contradiction in its approved PRD, which an amendment, approved alone, settled. `close` wrote the Merge
>   order with every row at its Target. Each member's agent steps ran in a session started in its own root.
> - **Q3.** After Q2's greet session ended at `verified`, a fresh session resumed from the record alone and ran
>   greet's staging deploy (after F-3; the first try, Q3a, was refused and found F-3).
> - **Q4.** `check` exits 1 in both repositories. With greet moved away, the client's `check` exits 3, and its
>   `prd-lint` job's commands all exit 0.
> - **Q5.** greet's change-set branch from Q2's close, squash-merged into `main`: the client's `check` flagged
>   `orphaned lock`, and `sync` cleared it.
> - **Q6.** With the client clone moved away, `impact` exits 3, and the change stops at the hand-off without
>   skipping the client.
>
> **Scope.** Two sibling scratch repositories, `<scratch>/greet` and `<scratch>/greet-client`, built by
> `link_repo.py <scratch>/greet-client unlinked --upstream <scratch>/greet`. Neither has a remote, and nothing
> was pushed. Deploys went only to greet's local `.deploy/staging`.

**Attempts.**
- **Attempt 1** (`<scratch>/attempt1/`, session Q1a) stopped at Q1's dry run on two gaps in the scaffold PRD:
  - What the relative GREET path is relative to.
  - What a system test does when `TEST_ENV` is unset.

  This is F-1, fixed in f6f2607. Q1 reran from a fresh scaffold.
- **Attempt 2** ran Q1 to its pass (sessions Q1a to Q1e, kept as the Q1 proof), then Q2 to step 3 (sessions in
  `<scratch>/attempt2/`). That record wrote greet's row Version as `1.1.0`, with no `→`: F-2, fixed in 24273b1.
- **Attempt 3** restarted Q2 from the after-Q1 state, with the toolkit re-vendored (R-4).
  - Q3a was refused at greet's staging deploy: F-3, ruled R-13a and fixed in f0b023c.
  - The proof then resumed in place from Q3's start state, re-vendored again (R-5): Q3b, then Q2f to Q2h.
  - Q4, Q5 and Q6 ran on their own copies.
- All repositories, transcripts and state tarballs are kept under `<scratch>/`.

## Run setup

- **Start state.** `python3 -B prd-toolkit/evals/scaffolds/link_repo.py <scratch>/greet-client unlinked --upstream
  <scratch>/greet`, with exit 0. `git remote -v` prints nothing in either repository, before and after the run.
  The client's Location for greet is `../greet`.
- **Sessions.**
  - Headless `claude -p` (Claude Code 2.1.316), `--model sonnet`, `--output-format stream-json --verbose`.
  - `--plugin-dir` is this branch's `prd-toolkit`, with the installed copy disabled.
  - The allowed tools are `Read Glob Grep Write Edit Bash Agent Skill`, with no permission-bypass flag.
  - Each init event shows `prd-toolkit@inline` 0.7.0, and its slash-command list holds
    `prd-toolkit:prd-change-set`. Commands use the `prd-toolkit:<command>` form (O-a).
  - One session ran at a time, each from the repository its step names (R-11c).
- **Files.**
  - Each session's prompt, stream and stderr: `<scratch>/proof/<id>.prompt.md`, `.jsonl` and `.stderr`.
  - `<id>.resume` names the session a reply resumed (R-1).
  - State tarballs: `start-unlinked`, `after-q1`, `q2-start`, `q2-approved`, `q3-start`, `q3b-start`,
    `q2f-start`, `q2g-start` and `q2-closed`, each `.tgz`.
  - Full-suite logs: `suite-F1.txt`, `suite-F2.txt` and `suite-F3.txt`.
- **Owner's replies.** Sent under the approved plan's authorization, each after the stop it answers, naming its
  run:
  - `approved`, in Q1b: a fresh session after Q1a's report. It re-ran the dry run and asked again (R-1).
  - `approved`, in Q1c: Q1b resumed, after Q1b showed its report.
  - `approved`, in Q1e: Q1d resumed, for greet's Consumers-row patch (R-2).
  - `yes, greet and greet-client are the members`, twice: attempt 2's Q2b and attempt 3's Q2b, each resuming its
    Q2a after the `impact` lines and the proposed members were shown.
  - `approved`, in Q2d: Q2c resumed, after both members' PRD diffs were shown together. This is the one approval
    of CS-001.
  - In Q2g, resuming Q2f after its build stopped on the PRD contradiction: "The banner is
    `*** <greeting>, <name>! ***`, built from the JSON's `greeting` and `name`, so T-001.1's `*** Hi, World! ***`
    is right. Amend AC-001.1, AC-001.2 and the glossary to say so." (R-6)
  - In Q2h, resuming Q2g after the amendment's diff and dry run were shown: "approved; remove the stale
    tests/system/test_welcome_staging.py and discard the old builder branch". This is the amendment's own
    approval.

  No other reply was sent. No `deploy production` was needed, because Q2's Target is staging.

## Sessions

| Session | Repo | Command | Outcome | Commits (scratch) |
|---|---|---|---|---|
| Q1a (att. 1) | greet-client | `prd-toolkit:prd-change` cite `cli:greet/greet` | dry run of T-001.2 failed on 2 scaffold gaps (F-1) | — |
| Q1a | greet-client | same prompt, fixed scaffold | `add` both sides, `sync`, 1.0.1 drafted, dry run passed; stopped for approval | — |
| Q1b | greet-client | `approved` (fresh) | re-ran the dry run (pass), asked again (R-1) | — |
| Q1c | greet-client | `approved` (resume Q1b) | Approved 1.0.1 | 2dd38db |
| Q1d | greet | `prd-toolkit:prd-change` record the Consumers row | 1.0.2 patch drafted, `impact` 0; stopped for approval | — |
| Q1e | greet | `approved` (resume Q1d) | Approved 1.0.2 | da2f406 |
| Q2a | greet | `prd-toolkit:prd-change-set <greet --json …>` | FR-003 edited; `impact` exit 1 names the client; stopped for members | — |
| Q2b | greet | the members reply (resume) | `changeset new`; branches in both; greet in review; set; log; stopped for the client's step 2 | 68bf802, 822c01f, 4e0563b, 28be79a |
| Q2c | greet-client | `prd-toolkit:prd-change-set CS-001` | client 2.0.0 edited, `sync --ref`, lint 0, dry run passed; both diffs shown; stopped for the approval | 91c6325; record 431f898 |
| Q2d | greet-client | `approved` (resume Q2c) | `changeset approve`; both members' approval commits; stopped for greet's build | 5894e86, 850ebe2, 1f69f76, 6cfef44 |
| Q2e | greet | `prd-toolkit:prd-change-set CS-001`, end once greet is verified (R-3) | `/prd-build` FR-003: builder, 5 unit passed, trace 0; `state=verified`; ended | 3f3e676, 146b103, a263d6f |
| Q3a | greet | `prd-toolkit:prd-change-set CS-001` (fresh) | resumed from the record; `/prd-deploy --until staging` refused by the pre-flight (F-3) | — |
| — | (driver) | F-3 fixed (f0b023c); re-vendored (R-5) | — | 2e7d689 (greet), 024c54d (client) |
| Q3b | greet | `prd-toolkit:prd-change-set CS-001` (fresh) | **Q3**: resumed from the record; staging deploy done with `drift allowed by greet/CS-001: …`; `state=live in staging`; stopped for the client's build | 7aee229, 5ae3427, caa5448 |
| Q2f | greet-client | `prd-toolkit:prd-change-set CS-001` | sync re-lock; `/prd-build welcome FR-001`; builder and tester; stopped on a PRD contradiction before the merge; `changeset stop` | 691aca5; record c9265f6 |
| Q2g | greet-client | the owner's answer (resume Q2f) | amendment drafted: 3.0.0, AC-001.1, AC-001.2, T-001.2, glossary; dry run passed; stopped for its approval | — |
| Q2h | greet-client | the amendment's approval (resume Q2g) | `approve --amendment`; approval commit; rebuild; FR-001 `verified`; `close`, Merge order | 4bd8a54, 734a06c, 761ae6c, d0ded99, d4affe2; record 4cfef3a, 9bf0324, 6a3e17a |
| — | (driver) | Q4 on a copy of `q2-start` | see Q4 | 8f58969 (greet), CI include (client) |
| — | (driver) | Q5 on a copy of `q2-closed` | see Q5 | squash 3d1d6d4; re-lock |
| Q6a | greet (client moved away) | `prd-toolkit:prd-change` usage on stderr | `impact` exit 3; handed to `prd-toolkit:prd-change-set`; stopped at step 1 | — |

## Pass lines

| # | Pass line (spec §13) | Result |
|---|---|---|
| Q1 | `add` writes both sides; `sync` copies only the `greet` key; both repositories' lint and `check` exit 0 | **Pass (R-2).** Q1a's `add`: `links.md: added Upstreams row greet \`../greet\`` and `../greet/docs/prd/greet/links.md: added Consumers row greet-client \`../greet-client\``, exit 0. `sync`: `wrote contracts/upstream/greet/cli.yaml`, whose only top-level key is `greet`, under the header `# Snapshot of greet 1.0.1 at e3dc6b3…, written by prd_links.py sync. Do not edit. Type: cli.` After Q1c (2dd38db) and Q1e (da2f406), greet gives lint 0 and `check` 0 (`consumer greet-client cli:greet: same`). greet-client gives lint 0 and `check` 0 (`upstream greet cli:greet: same`). Both note `newer than lock`, which is not drift. Trace 0 in both. Before Q1e, the client's `check` exited 1 (`upstream greet: missing row`), because greet's links.md was uncommitted on greet's `main`. |
| Q2 | `impact` names the client; CS-001 written; both PRDs edited and approved by one reply; `greet` built, deployed to staging; the client synced and built; `close` writes the Merge order; every row at its Target, with a resume in `greet-client`'s own session for the steps that dispatch agents there | **Pass (after F-2 and F-3).** Evidence: <br>• **impact:** Q2a gave `changed: cli:greet`, `consumer greet-client: cli:greet`, `prd-links-exit=1`. <br>• **CS-001:** Order greet, greet-client; Waits for `greet live in staging`; Targets `live in staging`, `verified`. <br>• **Edits and approval:** both PRDs were edited in their own sessions (the client's in Q2c, with `sync --ref` and its dry run) and committed `In review`. One reply became `Approval: 2026-11-02, "approved"`, then both approval commits. <br>• **greet built:** Q2e: 3f3e676 carries `Refs: FR-003`, `Change-set: greet/CS-001`; `verified`. <br>• **greet deployed:** Q3b, run `20261103T011856Z-staging`, `prd-deploy: done step=2`; the staging row `\| staging \| 1.1.0 \| 2e7d689 \| 2026-11-03 \| 20261103T011856Z-staging \|`; `state=live in staging`. <br>• **Client synced and built:** in its own session, Q2f to Q2h. The first build stopped on a contradiction in the approved PRD: T-001.1 expected `*** Hi, World! ***`, while AC-001.1 gave `*** <greeting> ***`. `changeset stop` recorded it. An amendment, its diff shown and approved alone (`Approval: … (amendment)`), took the client to 3.0.0. The rebuild (761ae6c, `Refs: FR-001`, `Change-set: greet/CS-001`) passed 3 unit tests with trace 0, and FR-001 went `verified`. <br>• **Close:** `Status: done`, rows `live in staging` / `live in staging` and `verified` / `verified`, then `## Merge order` `1. greet (cs-001-…)`, `2. greet-client (cs-001-…)`. <br>• **Afterwards:** lint and trace 0 in both. The client's code against greet's staging install prints `*** Hi, World! ***`. |
| Q3 | Q2's session ended once `greet` is `verified`: a new session resumes from the record alone and continues with `greet`'s staging deploy | **Pass (after F-3).** Q2e ended after `state=verified`, recorded (a263d6f). Q3b, a fresh session given only `prd-toolkit:prd-change-set CS-001`, Read the procedure and then the record, and called `prd-toolkit:prd-deploy --until staging`. Its `run` printed `drift allowed by greet/CS-001: consumer greet-client cli:greet: changed`, `run: 20261103T011856Z-staging`, `prd-deploy: done step=2 run=20261103T011856Z-staging`. `prd_deploy.py check` exited 0, then `changeset set greet 'state=live in staging'` and the log of the client's hand-off. Q3a, the same resume before the fix, was refused (`refused: prd_links check found drift: greet-client cli:greet`, `prd-deploy-exit=1`): F-3. |
| Q4 | An edit to `greet`'s `cli.yaml` outside a change set: `check` exits 1 in both repositories; with `greet` moved away, the client's `check` exits 3 and its CI job passes | **Pass.** On a copy of `q2-start`, greet commit 8f58969 (hooks on) changed exit code 2's text. greet's `check`: `consumer greet-client cli:greet: changed`, exit **1**. The client's: `upstream greet cli:greet: changed`, exit **1**. With greet moved away, the client's `check` printed `upstream greet: unreachable (\`../greet\` is unreachable: no directory …)` and exited **3**. `prd_hooks.py ci --github` wrote the `prd-lint` job, and its three `run:` lines, run locally with greet away, each exit **0**: `prd_lint.py --ci`, `prd_hooks.py check --ci`, and `prd_links.py check --ci` (which printed the unreachable line). |
| Q5 | `greet`'s change-set branch squash-merged into `main`: `check` flags the orphaned lock; `sync` clears it | **Pass.** On a copy of `q2-closed`, greet ran `git merge --squash cs-001-…` plus a commit (3d1d6d4), and the branch was deleted. The client on its branch, locked at greet 4cfef3a: `upstream greet: orphaned lock`, exit **1**. `sync docs/prd/greet-client greet`: `links.md: locked greet 1.1.0 at 3d1d6d4… (main)`, exit 0. `check`: `upstream greet cli:greet: same`, exit **0**. The re-lock was committed (`Refs: none (no behaviour change)`, the trailer), and lint stayed 0. An earlier provisional run on `q3-start` gave the same three results. |
| Q6 | `/prd-change` in `greet` touching `cli:greet` with the client clone moved away: `impact` exits 3; the change stops and hands off without skipping the client | **Pass.** Q6a: `consumer greet-client: unreachable`, `prd-links-exit=3`. The session handed off to `prd-toolkit:prd-change-set` with the edits in the tree. Its step 1 re-ran `impact` (exit 3 again) and stopped: "Either make `../greet-client` available … or tell me in your own words that it stays out of this change." Nothing was committed, no record or branch was made, and the client was never skipped. |

## Rulings (this run)

- **R-1: a reply goes to the session that showed what it approves.** `changing-prds` step 5 counts only a
  dry-run report held by its own conversation ("a new session starts with neither").
  - A fresh session sent `approved` (Q1b) re-ran the dry run and asked again: "Your "approved" came before I had a
    dry-run report for the current files, so I re-ran the dry run first."
  - Every later reply was sent as a new `claude -p --resume <stopped session>` invocation, after that session's
    stop. Q3's sessions alone are fresh, by its pass line.
- **R-2: the upstream's Consumers row is its own PRD change.** `add` writes it into greet's working tree. Q1a's
  session said "That file is a PRD change in greet's repository. It needs its own patch bump and approval there",
  so Q1d ran `prd-toolkit:prd-change` in greet for it. Spec §3 makes a link part of a PRD change with its bump,
  and the client's `check` reads greet at its default branch, so Q1's "`check` exits 0 in both" needs that commit.
  See O-1.
- **R-3: Q2e's prompt carried the owner's leaving.** It said to end the session once greet's row was `verified`.
  `--until staging` has no human step, so Q3 has no natural stop to start from.
- **R-4: after F-2, Q2 reran from the after-Q1 state, re-vendored.** It did not rerun Q1. The plugin's
  `prd_hooks.py check` named only `.prd-toolkit/prdlint/changeset.py` as differing in each repository.
  `prd_hooks.py install` refreshed it, committed with `Refs: none (no behaviour change)` (13f15da greet, 102cba4
  client). This is the 0.6 Q1b procedure.
- **R-5: after F-3, the proof resumed in place.** Q2 and Q3 were not rebuilt, because the state was clean: Q3a
  had refused before step 1 and written nothing. `prd_hooks.py check` named only `.prd-toolkit/prd_deploy.py` and
  `.prd-toolkit/prdlint/deploy.py`. `install` refreshed them, committed on the change-set branch with
  `Refs: none (no behaviour change)` and the trailer (2e7d689, 024c54d). Q3 was then judged on Q3b, a fresh
  session from that state.
- **R-6: the owner's answer to Q2f's stop.**
  - Q2f stopped on a contradiction the session had written into the approved PRD in Q2c. The stop asked which
    output is meant.
  - The answer sent is the scaffold's own text for this change. `link_repo.py`'s `CLIENT_JSON_AC` reads "print
    `*** <greeting>, <name>! ***` from the `greeting` and `name` of its JSON output".
  - The fix went through step 5's amendment: edit, dry run, its diff shown, and approved alone.
- **R-13a (controller, F-3).** The deploy pre-flight lets a drift line through when an open record (Status not
  `done` or `abandoned`, under the PRD's own `changes/` or in a repository its links point to) lists both this PRD
  and the drifting side. It prints `drift allowed by <start-prd>/CS-nnn: <line>`. Any other drift still refuses,
  and `check` and CI are unchanged. Spec §8 and its Revisions, and the README's Change sets, say so.

## Findings

| ID | Finding | Disposition |
|---|---|---|
| F-1 | The scaffold's client `testing.md` left two gaps a dry run of T-001.2 must answer: what GREET's path is relative to, and an unset `TEST_ENV`. Q1's change could not pass its dry run (attempt 1). | Fixed in f6f2607 (`link_repo.py`, pinned in `test_link_repo.py` first). Q1 reran from a fresh scaffold; its dry run passed with each question dismissed by a quote. |
| F-2 | `changeset new` read each member's `version:` from its working tree. Step 1 leaves the change's edits there, the bump among them, so greet's row read `1.1.0`, and `set version=1.1.0` wrote no `→`. **Where to enter** then reads greet's step 2 as not done (attempt 2). | Fixed in 24273b1: the version comes from the member's default branch, where its branch is cut (`test_new_reads_each_version_where_the_branch_is_cut` failed first). Q2 reran (R-4): `1.0.2 → 1.1.0`. |
| F-3 | The deploy pre-flight runs `prd_links.py check`, whose Consumers side reads greet-client at its default branch, where the snapshot is greet 1.0.1. greet's change-set edit of `cli:greet` was therefore `changed` (exit 1), which refused the run. But §6 step 4 needs the upstream's `/prd-deploy --until <env>` before a downstream that waits for `live in <env>` builds, so every such change set deadlocked. Q3a: `refused: prd_links check found drift: greet-client cli:greet`, `prd-deploy: refused step=0 run=none`, `prd-deploy-exit=1`. | Ruled R-13a (option A, scoped) and fixed in f0b023c. Eight tests went in first: let-through with an open record found through links.md and with its own; refused when the record is `done` or `abandoned`, when either side is not a member, or with no record; the run prints each let-through line. The fix commit also carries the spec Revision, the §8 sentence and the README line. Proven by Q3b (`drift allowed by greet/CS-001: consumer greet-client cli:greet: changed`, then `done`). |

**Observations (minor, not fixed; none blocks a pass line).**
- **O-1: no skill text names `add` for a change, or the upstream-side patch.** `changing-prds` never says
  `prd_links.py add`; Q1a found it in `references/prd-format.md` and `--help`. The Consumers row it writes into
  the upstream is left for a separate change. Q1a's report said so, but Q1c's close did not repeat it. Q1d's §14
  row did not say `format: links.md (prd-toolkit 0.7)`, and lint does not require it.
- **O-2: a custom-type snapshot is re-serialized YAML, not a verbatim copy.** The `output:` line comes back folded
  over two lines and unquoted. §4 says "copied verbatim"; `check` compares by value and says `same`.
- **O-3: procedure drift.** Sessions chained commands with `;` and `&&`, used `$G` shell variables and `cd`, and
  appended `ls` or `cat` to gated calls (Q1a, Q1c, Q2c in attempts 2 and 3). Every gate value was still read. No
  effect on any outcome.
- **O-4: both Q2a sessions bumped the version before `changeset new`.** Step 1 runs only `changing-prds` steps 1
  and 2. This is what exposed F-2, and after the fix it is harmless.
- **O-5: a pre-flight refusal exits 1, not 2.** §8 says the pre-flight refuses with exit 2, but the run gave
  `prd-deploy-exit=1`, `refused step=0`. Not decided here.
- **O-6: Q2e misstated the deploy.** Its close said "the deploy has human steps"; `--until staging` has none (Q3a's
  plan).
- **O-7: some first `result` events came early.** Q1a, Q2c, Q2e, Q2f and Q2g each emitted one while their agent
  ran in the background. The process went on and finished in the same run, with no effect.
- **O-8: the amendment bumped the unlanded 2.0.0 to 3.0.0.** Two majors went into one change set: the record row
  reads `1.0.1 → 3.0.0`, and §14 holds both rows. The text does not say whether an amendment to an unlanded
  version revises it in place.
- **O-9: the dry run cannot catch a contradiction between an AC and a unit case.** Q2c's dry run passed:
  T-001.1 is a unit case and was never sampled, while T-001.2 [system] said nothing on the banner. The build's
  reconciliation caught it and stopped, as designed.

**What held.**
- No request was taken as an approval or a members reply, and every stop waited for its reply.
- A step that dispatches agents always ran from its member's root: the client's step 2, its dry run and both
  builds in client sessions, greet's build in a greet session. The record's Log names each hand-off.
- A stop went on Status with the row's State kept (`stopped: greet-client: …`, the row still `approved`), and the
  next `set` moved it back to running.
- No snapshot was edited by hand: every one was written by `sync`.
- Nothing was pushed or merged by a session. `close` wrote the Merge order, and the session told the owner to
  land greet first.

## O-a

Question (carried from 0.5): does a bare `/prd-*` slash command register in a headless `--plugin-dir` run?

Probe, run 2026-11-02 with Claude Code 2.1.316, in a scratch repo built by
`python3 -B prd-toolkit/evals/scaffolds/deploy_repo.py <scratch> ready`:

```
claude -p "/prd-status docs/prd/greet" --plugin-dir <worktree>/prd-toolkit \
  --settings '{"enabledPlugins":{"prd-toolkit@ihistand":false}}' \
  --model sonnet --output-format stream-json --verbose
```

Finding: **the bare command did not register; the namespaced form did.**

- The `init` event's `slash_commands` list (135 entries) held no bare `prd-status`. Its entries matching `prd`, verbatim:

  ```
  ["prd-toolkit:prd-adopt", "prd-toolkit:prd-build", "prd-toolkit:prd-change", "prd-toolkit:prd-context", "prd-toolkit:prd-deploy", "prd-toolkit:prd-error", "prd-toolkit:prd-new", "prd-toolkit:prd-publish", "prd-toolkit:prd-status", "prd-toolkit:adopting-prds", "prd-toolkit:authoring-prds", "prd-toolkit:building-from-prds", "prd-toolkit:changing-prds", "prd-toolkit:deploying-from-prds", "prd-toolkit:handling-errors", "prd-toolkit:publishing-prds", "prd-toolkit:testing-from-prds"]
  ```

  It held the
  namespaced `prd-toolkit:prd-adopt`, `prd-build`, `prd-change`, `prd-context`, `prd-deploy`,
  `prd-error`, `prd-new`, `prd-publish` and `prd-status`, plus the eight skills as
  `prd-toolkit:<skill>`. The plugin loaded as `prd-toolkit@inline` version 0.6.1.
- The session's first turn was `Skill` with `{"skill":"prd-toolkit:prd-status","args":"docs/prd/greet"}`:
  the model mapped the bare text onto the namespaced command, which expanded to the status prompt.
  It then ran `uv run --script .prd-toolkit/prd_status.py docs/prd/greet` (exit 0) and printed the report.
- So `/prd-status` worked end to end, but through the `prd-toolkit:prd-status` skill call, not as a
  registered bare command. The README's headless note (Task 12) should give the
  `prd-toolkit:<command>` form.
- This run used the namespaced form throughout (`prd-toolkit:prd-change`, `prd-toolkit:prd-change-set`), and every
  session's init listed it; `running-a-change-set.md` itself invokes `prd-toolkit:prd-build` and
  `prd-toolkit:prd-deploy` through the Skill tool.
