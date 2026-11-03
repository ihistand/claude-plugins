# prd-toolkit 0.7 acceptance run

> **Date:** 2026-11-02
> **Spec:** `2026-11-02-prd-toolkit-0.7-design.md`, §13 (Q1 to Q6), with §6 (its **Sessions** paragraph) and the
> Revisions block
> **Result:** **stopped at Q3 on F-3, which needs a design decision** (NEEDS_CONTEXT). Q1, Q4 and Q6 pass. Q5's
> mechanism passes on a provisional start state. Q2 and Q3 hold up to greet's staging deploy, which the deploy
> pre-flight refuses inside every change set whose downstream waits for `live in <env>`.
> - **Q1.** `add` wrote both sides, `sync` copied only the `greet` key, and lint and `check` exit 0 in both
>   repositories, after the upstream's Consumers row went through its own `/prd-change` in greet (R-2).
> - **Q2.** `impact` named the client. CS-001 was written, both PRDs were edited, and both were approved by one
>   reply. greet was built and `verified`, with a resume per member. Then **F-3**: greet's
>   `/prd-deploy --until staging` was refused before step 1 (`refused: prd_links check found drift: greet-client
>   cli:greet`). The client build, the close and the Merge order were not reached.
> - **Q3.** A fresh session resumed from the record alone and went straight to greet's staging deploy, which F-3
>   refused.
> - **Q4.** `check` exits 1 in both repositories. With greet moved away, the client's `check` exits 3, and its
>   `prd-lint` job's commands all exit 0.
> - **Q5 (provisional).** On greet's change-set branch at Q3's start (built, not deployed), squash-merged into
>   `main`: the client's `check` flags `orphaned lock` (exit 1), and `sync` clears it (`check` exit 0). Rerun it
>   on Q2's closed branch once F-3 is settled.
> - **Q6.** With the client clone moved away, `impact` exits 3, and the change stops at the hand-off without
>   skipping the client.
>
> Three toolkit defects were found. F-1 and F-2 are fixed on the branch. F-3 is open.
>
> **Scope.** Two sibling scratch repositories, `<scratch>/greet` and `<scratch>/greet-client`, built by
> `link_repo.py <scratch>/greet-client unlinked --upstream <scratch>/greet`. Neither has a remote, and nothing
> was pushed. Deploys go only to local `.deploy/<env>` installs.

**Attempts.**
- **Attempt 1** (`<scratch>/attempt1/`, session Q1a) stopped at Q1's dry run on two gaps in the scaffold PRD:
  - What the relative GREET path is relative to.
  - What a system test does when `TEST_ENV` is unset.

  This is F-1, fixed in f6f2607. Q1 reran from a fresh scaffold.
- **Attempt 2** ran Q1 to its pass (sessions Q1a to Q1e, kept as the Q1 proof), then Q2 to step 3 (sessions in
  `<scratch>/attempt2/`). That record wrote greet's row as `1.1.0`, with no arrow: F-2, fixed in 24273b1.
- **Attempt 3** restarted Q2 from the after-Q1 state, with the toolkit re-vendored (R-4). It ran through Q3a,
  which stopped on F-3. Q4, Q5 and Q6 ran on their own copies.
- All repositories, transcripts and state tarballs are kept under `<scratch>/`.

## Run setup

- **Start state.** `python3 -B prd-toolkit/evals/scaffolds/link_repo.py <scratch>/greet-client unlinked --upstream
  <scratch>/greet`, with exit 0. `git remote -v` prints nothing in either repository. The client's Location for
  greet is `../greet`.
- **Sessions.**
  - Headless `claude -p` (Claude Code 2.1.316), `--model sonnet`, `--output-format stream-json --verbose`.
  - `--plugin-dir` is this branch's `prd-toolkit`, with the installed copy disabled.
  - The allowed tools are `Read Glob Grep Write Edit Bash Agent Skill`, with no permission-bypass flag.
  - Each init event shows `prd-toolkit@inline` 0.7.0. Commands use the `prd-toolkit:<command>` form (O-a).
  - One session ran at a time, each from the repository its step names (R-11c).
- **Files.**
  - Each session's prompt, stream and stderr: `<scratch>/proof/<id>.prompt.md`, `.jsonl` and `.stderr`.
  - `<id>.resume` names the session a reply resumed (R-1).
  - State tarballs: `start-unlinked.tgz`, `after-q1.tgz`, `q2-start.tgz`, `q2-approved.tgz` and `q3-start.tgz`.
  - Full-suite logs: `suite-F1.txt` and `suite-F2.txt`.
- **Owner's replies.** Sent under the approved plan's authorization, each after the stop it answers, naming its
  run:
  - `approved`, in Q1b: a fresh session after Q1a's report. It re-ran the dry run and asked again (R-1).
  - `approved`, in Q1c: Q1b resumed, after Q1b showed its report.
  - `approved`, in Q1e: Q1d resumed, for greet's Consumers-row patch (R-2).
  - `yes, greet and greet-client are the members`, twice: attempt 2's Q2b and attempt 3's Q2b, each resuming its
    Q2a after the `impact` lines and the proposed members were shown.
  - `approved`, in attempt 3's Q2d: Q2c resumed, after both members' PRD diffs were shown together. This is the
    one approval of CS-001.

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
| Q2b | greet | the members reply (resume) | `changeset new`; branches in both; greet in review; set; log; stopped for the client's step 2 | 4 record/PRD commits |
| Q2c | greet-client | `prd-toolkit:prd-change-set CS-001` | client 2.0.0 edited, `sync --ref`, lint 0, dry run passed; both diffs shown; stopped for the approval | in review, record |
| Q2d | greet-client | `approved` (resume Q2c) | `changeset approve`; both members' approval commits; stopped for greet's build | 4 |
| Q2e | greet | `prd-toolkit:prd-change-set CS-001`, end once greet is verified (R-3) | `/prd-build` FR-003: builder, 5 unit passed, trace 0; `state=verified`; ended | 3f3e676, 146b103, a263d6f |
| Q3a | greet | `prd-toolkit:prd-change-set CS-001` (fresh) | resumed from the record; `/prd-deploy --until staging` **refused by the pre-flight (F-3)**; stopped and asked | — |
| — | (driver) | Q4 on a copy of `q2-start` | see Q4 | 8f58969 (greet), CI include (client) |
| — | (driver) | Q5 on a copy of `q3-start` | see Q5 | squash 89ee194, re-lock |
| Q6a | greet (client moved away) | `prd-toolkit:prd-change` usage on stderr | `impact` exit 3; handed to `prd-toolkit:prd-change-set`; stopped at step 1 | — |

## Pass lines

| # | Pass line (spec §13) | Result |
|---|---|---|
| Q1 | `add` writes both sides; `sync` copies only the `greet` key; both repositories' lint and `check` exit 0 | **Pass (R-2).** Q1a's `add`: `links.md: added Upstreams row greet \`../greet\`` and `../greet/docs/prd/greet/links.md: added Consumers row greet-client \`../greet-client\``, exit 0. `sync`: `wrote contracts/upstream/greet/cli.yaml`, whose only top-level key is `greet`, under the header `# Snapshot of greet 1.0.1 at e3dc6b3…, written by prd_links.py sync. Do not edit. Type: cli.` After Q1c (2dd38db) and Q1e (da2f406), greet gives lint 0 and `check` 0 (`consumer greet-client cli:greet: same`). greet-client gives lint 0 and `check` 0 (`upstream greet cli:greet: same`). Both note `newer than lock`, which is not drift. Trace 0 in both. Before Q1e, the client's `check` exited 1 (`upstream greet: missing row`), because greet's links.md was uncommitted on greet's `main`. |
| Q2 | `impact` names the client; CS-001 written; both PRDs edited and approved by one reply; `greet` built, deployed to staging; the client synced and built; `close` writes the Merge order; every row at its Target, with a resume in `greet-client`'s own session for the steps that dispatch agents there | **Not reached: stopped on F-3.** What held: `impact` gave `changed: cli:greet` / `consumer greet-client: cli:greet`, `prd-links-exit=1`. CS-001 is in greet, Order greet then greet-client, Waits for `greet live in staging`, Targets `live in staging` and `verified`, Versions `1.0.2 → 1.1.0` and `1.0.1 → 2.0.0` (after F-2). The client's step 2 and its dry run ran in its own session (Q2c), from the record. One reply became `Approval: 2026-11-02, "approved"`, and both members' approval commits carry `Change-set: greet/CS-001`. greet was built in its own session (Q2e): the builder commit 3f3e676 carries `Refs: FR-003` and `Change-set: greet/CS-001`, trace 0, and the row went `verified`. **Failed:** greet's staging deploy (F-3). Not reached: the client build, `close`, the Merge order. |
| Q3 | Q2's session ended once `greet` is `verified`: a new session resumes from the record alone and continues with `greet`'s staging deploy | **Resume held; the deploy was refused (F-3).** Q3a, a fresh session given only `prd-toolkit:prd-change-set CS-001`, Read the procedure, Globbed `docs/prd/*/changes/CS-001.md`, Read the record, and called `prd-toolkit:prd-deploy --until staging` next, with no other context. The plan showed two agent steps. `run` then printed `refused: prd_links check found drift: greet-client cli:greet`, `prd-deploy: refused step=0 run=none`, `prd-deploy-exit=1`. The session did not retry or work around it, edited no snapshot, and asked. |
| Q4 | An edit to `greet`'s `cli.yaml` outside a change set: `check` exits 1 in both repositories; with `greet` moved away, the client's `check` exits 3 and its CI job passes | **Pass.** On a copy of `q2-start`, greet commit 8f58969 (hooks on) changed exit code 2's text. greet's `check`: `consumer greet-client cli:greet: changed`, exit **1**. The client's: `upstream greet cli:greet: changed`, exit **1**. With greet moved away, the client's `check` printed `upstream greet: unreachable (\`../greet\` is unreachable: no directory …)` and exited **3**. `prd_hooks.py ci --github` wrote the `prd-lint` job, and its three `run:` lines, run locally with greet away, each exit **0**: `prd_lint.py --ci`, `prd_hooks.py check --ci`, and `prd_links.py check --ci` (which printed the unreachable line). |
| Q5 | `greet`'s change-set branch squash-merged into `main`: `check` flags the orphaned lock; `sync` clears it | **Pass on a provisional start state.** On a copy of `q3-start` (greet's branch built and `verified`, not deployed), `git merge --squash` plus a commit (89ee194) and the branch deleted. The client on its branch, locked at greet 28be79a: `upstream greet: orphaned lock`, exit **1**. Then `sync docs/prd/greet-client greet`: `links.md: locked greet 1.1.0 at 89ee194… (main)`, exit 0. Then `check`: `upstream greet cli:greet: same`, exit **0**. To be rerun on Q2's closed branch. |
| Q6 | `/prd-change` in `greet` touching `cli:greet` with the client clone moved away: `impact` exits 3; the change stops and hands off without skipping the client | **Pass.** Q6a: `consumer greet-client: unreachable`, `prd-links-exit=3`. The session handed off to `prd-toolkit:prd-change-set` with the edits in the tree. Its step 1 re-ran `impact` (exit 3 again) and stopped: "Either make `../greet-client` available … or tell me in your own words that it stays out of this change." Nothing was committed, no record or branch was made, and the client was never skipped. |

## Rulings (this run)

- **R-1: a reply goes to the session that showed what it approves.** `changing-prds` step 5 counts only a
  dry-run report held by its own conversation ("a new session starts with neither").
  - A fresh session sent `approved` (Q1b) re-ran the dry run and asked again: "Your "approved" came before I had a
    dry-run report for the current files, so I re-ran the dry run first."
  - Every later reply was sent as a new `claude -p --resume <stopped session>` invocation, after that session's
    stop. Q3 alone uses a fresh session, by its pass line.
- **R-2: the upstream's Consumers row is its own PRD change.** `add` writes it into greet's working tree. Q1a's
  session said "That file is a PRD change in greet's repository. It needs its own patch bump and approval there",
  so Q1d ran `prd-toolkit:prd-change` in greet for it. Spec §3 makes a link part of a PRD change with its bump,
  and the client's `check` reads greet at its default branch, so Q1's "`check` exits 0 in both" needs that commit.
  See O-1.
- **R-3: Q2e's prompt carried the owner's leaving.** It said to end the session once greet's row was `verified`.
  `--until staging` has no human step, so Q3 has no natural stop to start from.
- **R-4: Q2 reran from the after-Q1 state, re-vendored.** It did not rerun Q1. The plugin's `prd_hooks.py check`
  named only `.prd-toolkit/prdlint/changeset.py` as differing in each repository. `prd_hooks.py install`
  refreshed it, committed with `Refs: none (no behaviour change)` (13f15da greet, 102cba4 client). Afterwards
  `check` 0 in both. This is the 0.6 Q1b procedure.

## Findings

| ID | Finding | Disposition |
|---|---|---|
| F-1 | The scaffold's client `testing.md` left two gaps a dry run of T-001.2 must answer: what GREET's path is relative to, and an unset `TEST_ENV`. Q1's change could not pass its dry run (attempt 1). | Fixed in f6f2607 (`link_repo.py`, pinned in `test_link_repo.py` first). Q1 reran from a fresh scaffold; its dry run passed with each question dismissed by a quote. |
| F-2 | `changeset new` read each member's `version:` from its working tree. Step 1 leaves the change's edits there, the bump among them, so greet's row read `1.1.0`, and `set version=1.1.0` wrote no `→`. **Where to enter** then reads greet's step 2 as not done (attempt 2). | Fixed in 24273b1: the version comes from the member's default branch, where its branch is cut (`test_new_reads_each_version_where_the_branch_is_cut` failed first). Q2 reran (R-4): `1.0.2 → 1.1.0`. |
| F-3 | **Open, needs a design decision.** The deploy pre-flight runs `prd_links.py check`. Its Consumers side reads greet-client at its default branch (§5 Revision), where the snapshot is greet 1.0.1, so greet's change-set edit of `cli:greet` is `changed` (exit 1). §8 makes that refuse the run, while §6 step 4 needs the upstream's `/prd-deploy --until <env>` before a downstream that waits for `live in <env>` builds. Every such change set deadlocks before its upstream deploy, and the downstream's own deploy would meet the same refusal (`upstream greet: orphaned lock`, `changed`). Evidence: Q3a, `refused: prd_links check found drift: greet-client cli:greet`, `prd-deploy: refused step=0 run=none`, `prd-deploy-exit=1`. A manual `check` in greet gives `consumer greet-client cli:greet: changed`, exit 1. | Not fixed. Options, below. |

**F-3 options** (the spec settles none of them):
- **A. The pre-flight excuses drift between members of an open change set.** On a branch with an open record
  (`changes/CS-nnn.md` here, or a record a member's trailer points to) whose rows name the drifted consumer or
  upstream, drift on those items is reported and does not refuse. This is narrowest, and it matches
  `coordinating-prds` rule 4 ("a `check` that then reports an orphaned lock or `changed` items is expected until
  the upstream lands").
- **B. `check` reads a member consumer at the record's Branch.** Inside an open change set, the Consumers side
  reads the consumer at the record's Branch instead of its default branch. This revises the §5 Revision (default
  branch only). The downstream's own deploy would still see `orphaned lock` on its Upstreams side.
- **C. An explicit override.** `prd_deploy.py run --change-set <record>`, passed by `running-a-change-set.md`
  step 4, turns member drift into a report line. Same effect as A, but opt-in in the procedure, not inferred.
- **D. No deploy inside a change set.** Change §6 so a `live in <env>` wait is met only after the upstream lands.
  This drops Q2's "deployed to staging" from the change set.

**Observations (minor, not fixed).**
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
- **O-5: the refused run exited 1, not 2.** §8 says the pre-flight refuses with exit 2, but the run gave
  `prd-deploy-exit=1`, `refused step=0`. Not decided here.
- **O-6: Q2e misstated the deploy.** Its close said "the deploy has human steps"; `--until staging` has none (Q3a's
  plan).
- **O-7: some first `result` events came early.** Q1a, Q2c and Q2e each emitted one while their agent ran in the
  background. The process went on and finished in the same run, with no effect.

**What held.**
- No request was taken as an approval or a members reply.
- Every stop waited for its reply.
- A step that dispatches agents always ran from its member's root: the client's step 2 and dry run in Q2c,
  greet's build in Q2e. The record's Log names each hand-off.
- No snapshot was edited by hand, and nothing was pushed.

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
