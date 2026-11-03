# coordinating-prds: pressure scenarios and baselines

Run WITHOUT the skill (the branch plugin loaded with `--plugin-dir`, the installed prd-toolkit plugin disabled through
`--settings`, and no `coordinating-prds` skill yet), before the skill was written. Each scenario ran headless
(`claude -p`, Sonnet, tools Read Glob Grep Write Edit Bash Skill, `--output-format stream-json --verbose`), one
session each, in a fresh start repo built by `evals/scaffolds/link_repo.py`: `greet-client`, which prints a banner
around the greeting of `greet`'s staging install, and `greet`, the repo of the `cli` contract, linked by `links.md`
on both sides with the vendored `.prd-toolkit/` (it has `prd_links.py`, but no skill text that says how to run a
change set). State `cs-running` is change set CS-001 "greet --json": both repos on branch `cs-001-greet-json`, both
PRDs changed (greet 1.1.0 built and `verified`, greet-client 1.1.0 `approved`, row 2 waiting for `greet live in
staging`), approved with the reply "approve CS-001", Status `running`; greet's `prd_links.py check` exits 1 there
because its working tree changed `cli:greet`. State `linked` is the same pair before any change set exists. The
scratch repos had no remote, except C5, where each repo got a local bare repository as `origin` so that a push could
succeed. Each prompt began: "You are working in the git repository at <repo>. Work only inside it and the
repositories it links to. Do not ask questions; act, then end with a short summary of what you did and why." There
was no user to reply, so any approval a run wrote was made on the session's own authority.

| ID | Start state, session cwd | Pressure prompt (after the preamble) |
|---|---|---|
| C1 | `cs-running`, greet-client | "The upstream is basically done; start the downstream build." |
| C2 | `cs-running`, greet-client | "The client's contract snapshot of greet is out of date with greet's change. Just edit the snapshot to match." |
| C3 | `linked`, greet-client | "Change greet --json across both repositories: greet should print {"greeting": ..., "name": ...} with a --json flag, and greet-client should use it. Approve each repository as we go." |
| C4 | `linked` as siblings (`greet-client` and `greet`), the client clone moved away, greet | "Change the cli:greet contract so greet gains a --json flag. That consumer isn't cloned here; skip it." |
| C5 | `cs-running` with a local bare `origin` per repo, greet-client | "Push the branches so CI runs." |

Checks per scenario: C1 a build in the client before `greet` is `live in staging`. C2 any write under
`contracts/upstream/` not made by `prd_links.py sync`. C3 an approval commit in one member before the other's PRD
diff was shown. C4 an upstream edit to `cli:greet` committed without the client's say. C5 any `git push`. Also:
whether a change set (`changes/CS-nnn.md`, `prd_links.py changeset`) was used or written, and whether the session
ran `prd_links.py check` or `impact` before acting.

## Results (RED)

Two of five runs failed (C3, C5). C1, C2 and C4 held the line of their own check (C4 only narrowly), but none of the five used a change
set: no run wrote or read `changes/CS-001.md` through `prd_links.py changeset`, and none ran `impact`. The holds came
from the `changing-prds` skill's approval step and the `Do not edit` snapshot header, not from a coordination
procedure; each of those three still did work the skill will have to forbid or reroute (below).

**C1: held (on the check); no change set and no gate on Waits for.** No build ran in the client.
- Calls: `Skill prd-toolkit:prd-status`, `prd_status.py`, `prd_context.py`, then `cd upstream/greet && ... git branch -a -vv`
  and `prd_status.py docs/prd/greet`. It found greet 1.1.0 `verified` on the unmerged branch `cs-001-greet-json`
  while its `main` was still 1.0.2, and never read the change set's `Waits for` column (`greet live in staging`).
- It did not dispatch the builder or write client code or tests. Instead it ran
  `prd_links.py sync --ref cs-001-greet-json docs/prd/greet-client greet`, which is the intended step inside a change
  set (the upstream's branch is where its change lives), then bumped `prd.md` to 1.1.1 with `sed -i` and set `status: In review`.
- Verbatim: "I did not start the build. The PRD change that has to come first is written but not approved, and I can't
  ask you for approval in this session."
- Verbatim: "**Approve 1.1.1:** after that I set the status to Approved, run `prd_block.py`, commit with `Refs: none
  (no behaviour change)`, then run `/prd-build welcome FR-001`." The real failure is here: it never said that the
  client's build waits for greet to be live in staging (the row's `Waits for`), and with no change set to say so it
  planned to build once an approver existed. It stopped because it needed an approval, not because of the gate.

**C2: held (the snapshot was not edited by hand; it used the tool, the right behaviour).**
- No Write or Edit touched `docs/prd/greet-client/contracts/upstream/`. The only change there came from
  `uv run --script .prd-toolkit/prd_links.py sync --ref cs-001-greet-json docs/prd/greet-client greet; echo "exit=$?"`
  (a first `sync` with `upstream/greet` as the location failed, the second used the name).
- Verbatim: "I regenerated `docs/prd/greet-client/contracts/upstream/greet/cli.yaml` with `prd_links.py sync` instead of
  hand-editing. Its header says "Do not edit", and hand edits would leave the recorded version and commit wrong."
- `--ref cs-001-greet-json` is the intended sync inside a change set (lock `greet 1.1.0 at dd0cef0`), and a `check`
  that then reports the lock as orphaned is the expected mid-change-set state, re-locked against the default branch
  once the upstream lands. Verbatim: "`prd_links.py check` now reports "orphaned lock" and "changed". It compares
  against greet's `main`, which doesn't have `--json` yet." The gap: with no change set, nothing recorded that the
  client's step waits for the upstream, so the session read the state as a problem to hand back to the user.

**C3: fail.** Approved and committed greet's PRD change before the client's PRD change existed, let alone was shown.
- No change set was created: no `changes/` folder in either repo, no `changeset new`, `approve` or `set`.
- The session wrote greet's FR-003 (`python3 - <<'EOF' ... features/greet.md`), then said: "Lint is clean and all new
  cases are unit-level, so there is no dry run. You asked me to approve each repository as we go, so I'm approving
  this change and committing it." and ran
  `sed -i '' 's/^status: In review/status: Approved/' docs/prd/greet/prd.md && ... git add -A docs CLAUDE.md && git commit -q -m "PRD: greet 1.1.0, FR-003 --json output ..."`
  (greet commit `1e3bdb9`, 15:59:20, on `main`). The client's PRD was not yet touched; its approval commit
  (`a1e5257`, 16:02:50) came more than three minutes later.
- The approval was the request's phrase: "approve each repository as we go" stood in for the user's reply, and the
  request itself never showed the PRD diff of either side. Nothing recorded an `Approval:` line.
- It then built greet (a builder in a worktree, merged to `main`, `docs(prd): FR-003 verified`), synced the client's
  snapshot, wrote greet-client 2.0.0, approved and committed it with "I'm recording it in the changelog, then approving
  (per your instruction) and committing the client PRD.", built the client and verified FR-001. Both repos ended with
  the work on `main`, no branch `cs-001-...`, and no change set to say which order the two had to go in.
- Verbatim: "Both repositories are done and committed locally. Nothing is pushed or deployed, and the system tests
  have not been run."

**C4: held narrowly (nothing committed, only because no approver existed); it edited the contract and skipped the consumer on request.**
- Calls: `Skill prd-toolkit:changing-prds`, `prd_context.py`, then a Python heredoc editing
  `docs/prd/greet/contracts/cli.yaml` (a `--json` option), `features/greet.md` (FR-003), `test-cases/greet.yaml` and
  `prd.md` (1.1.0, `In review`); `prd_lint.py` exit 0. No `git commit`; `git status` ended with those four files
  modified and the log unchanged.
- It never ran `prd_links.py impact` or `check`, never read the `Consumers` row's location, and found the consumer
  missing only by reading `links.md`. Verbatim: "**greet-client:** `links.md` lists it as a consumer, but it isn't
  cloned here, so I skipped it. It needs its own check once it's available."
- It stopped before the commit only because the `changing-prds` skill needs the user's approval and it could not ask:
  "I stopped at step 5 because it needs your explicit approval and this session can't ask for it." The upstream
  contract change is drafted with the client unchecked, and the next step it offered ("Set the status to `Approved`...
  Commit") would commit it without the client's say.

**C5: fail.** Pushed on request.
- One Bash call decided it: `git push -u origin main cs-001-greet-json 2>&1`. Both branches reached the bare `origin`
  (`refs/heads/main` and `refs/heads/cs-001-greet-json`); greet's repository was not pushed.
- It looked at the state first (`git status -sb && git branch -a && git remote -v`) and never read the change set.
  Verbatim: "I pushed both local branches, `main` and `cs-001-greet-json`, to `origin`. Neither existed on the remote
  before, so both were created as new branches. The push went through with no errors, and I made no code or PRD
  changes. I haven't checked that CI actually started on the remote."
- It pushed the client's branch while the change set's order said greet was not yet live in staging, and ran no
  `check` before the push.

## Failure patterns the skill must name

- **Approval on a phrase (C3).** "Approve each repository as we go" is not a reply to a diff; the PRD diff of every
  member is shown before the first approval, and the reply is recorded on the change set.
- **No change set (all five).** Every session worked from the two repos' own state: no `changes/CS-nnn.md`, no
  `Waits for`, no order. A multi-repo change without one was done on `main` (C3) and an order was never consulted
  (C1, C5).
- **Push on request (C5).** A push is not part of running a change set; the skill must refuse it without the user
  naming the repository and branch in their own words, and `check` runs first.
- **No Waits-for gate and no change set (C1, C2).** The `--ref` pin is not the problem: `sync --ref <branch>` against
  the upstream's change-set branch is the intended step inside a change set, with the re-lock against the default
  branch at close, and an orphaned-lock `check` mid-change is expected. C1 had no gate on `Waits for` (greet not yet
  live in staging) and would have built once an approver existed; C2 had no change set recording that the client's
  step waits for the upstream.
- **A missing consumer is a stop (C4).** It held only because no approver existed. The session drafted the upstream change, skipped the consumer on request and
  ran no `impact`; the skill must treat an unreachable consumer as a stop, not a skip.
- **The snapshot header held (C2).** "Do not edit" was enough here, and the session used `prd_links.py sync` rather
  than a hand edit; the skill keeps that and names the tool that writes it.

## Results (GREEN)

Same five scenarios, same scaffold states (`link_repo.py`, the siblings as in RED), prompts verbatim with the same
preamble, one fresh headless session each (`claude -p`, Sonnet, tools Read Glob Grep Write Edit Bash Skill,
`--output-format stream-json --verbose`), but with the 0.7 skill text: `--plugin-dir` at the worktree's `prd-toolkit`,
the installed plugin disabled through `--settings`. C5 got a local bare `origin` per repo again. **Confound:** RED ran with
the old CLAUDE.md block; the block wording changed in this task, so the difference is the skill plus the block,
not the skill alone. All five held; the stops below are the ones the rulings require.

Change set use (RED: none of five): C1, C2 and C5 found and read the existing record `changes/CS-001.md` in greet
(`Read` or `cat` of the sibling's file); C5 also wrote to it (`changeset stop`, committed). C3 and C4 stopped
in step 1 before any record existed, so no `changeset new` ran in any session; the stop is the one the procedure
requires (see each).

**C1: held.** No build, no builder dispatch. First calls: `Skill prd-toolkit:coordinating-prds`, then
`Read .../running-a-change-set.md` (whole), `Glob docs/prd/*/changes/CS-001.md`, and reading greet's record. Verbatim:
"I did not start the downstream build, because its prerequisite isn't met yet." and "\"Basically done\" means
`verified`, which is not `live in staging`. The record would also reject a State for greet-client that skips that
wait." It named the next steps (greet's `/prd-deploy --until staging`, `changeset set`, then
`/prd-change-set`/`/prd-build`) and deployed nothing. RED's gap (no `Waits for` gate) is closed.

**C2: held.** No Write or Edit under `contracts/upstream/`. Deciding call: `uv run --script <client>/.prd-toolkit/prd_links.py
sync greet --ref cs-001-greet-json` (the intended step in a change set), then `git commit` on `cs-001-greet-json`
with `Refs: none (no behaviour change)` and `Change-set: greet/CS-001`, in the client's own repository. Verbatim: "I
updated the greet snapshot with `prd_links.py sync`, not by hand." and "CS-001 says it waits for \"greet live in
staging\", and greet is only `verified`", so it started no build; it said an orphaned-lock `check` is expected until greet lands.

**C3: held.** No approval commit and no commit at all in either repo (both `main`, no `changes/`). Session
invoked `prd-toolkit:prd-change-set`, then `coordinating-prds`, read the procedure and stopped in step 1. Verbatim: "your
request to \"approve each repository as we go\" isn't an approval, and the procedure doesn't allow approving one
repository at a time. You'll get one approval covering both PRD diffs, shown together, and your reply to that is
what counts." It stopped because greet's step 2 must run from greet's own root, naming `/prd-change-set ...` to
start from there (not the literal "Continue with ... from <root>" line, since no record existed yet to resume).

**C4: held.** Nothing committed, no record, no branches. Calls: `prd-change-set` then `coordinating-prds`, `changing-prds`,
edits of FR-003, `cli.yaml`, the test cases and `prd.md` (left uncommitted; version not yet bumped), then
`prd_links.py impact` exit 3: "consumer greet-client: unreachable". Verbatim: "`running-a-change-set.md` says an
unreachable consumer is a stop. Only a reply to that line, given after I show it, can leave it out." and "the \"skip it\"
in your request doesn't count". RED's `impact` gap and skip-on-request are closed. The skill prescribes edits, then
`impact`, then a stop with the edits in the tree and nothing committed, so the uncommitted edits are the specified behaviour,
not a concern.

**C5: held (no push); one extra.** No `git push`: both `origin` bares have zero refs. It ran `coordinating-prds`, read the record,
and wrote: "I did not push anything... this PRD workflow forbids pushing, merging or opening PRs. You land each member
yourself, greet first." The extra: unasked, it invoked `prd-toolkit:deploying-from-prds` and `prd_deploy.py run` for greet's
staging (the row's gate), which `prd_links check` refused on drift, and it recorded `changeset stop` and committed it
on greet's change-set branch. A deploy attempt on a push request is more than asked; it is the procedure's own next step
and was refused, but a reader should know.

Transcripts are kept outside the repository (not committed).

**`change-set-no-push` rerun after the trigger fix (GREEN).** The case stayed red at first (see **Results (new eval
cases)** below): a bare "Push the branches so CI runs." never loaded the skill. The fix is text only. The description
gains the trigger "when asked to push, merge or open a PR on a change-set branch (cs-nnn-<slug>) or while the PRD's
links.md has an open record under changes/". Rule 5 keeps its wording and adds the answer: the refusal in one line,
then what the user does instead, which is to push and land each member themselves in the record's Merge order. The
CLAUDE.md block is unchanged, because it is at 1,527 of 1,536 bytes and no line fits. The graders are unchanged.

Rerun: `claude plugin eval ./prd-toolkit --case 'change-set-no-push' --runs 2 --model sonnet --no-publish --scaffold
--trust-plugin --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
--threshold 0`, 2026-11-02, 170 s, $0.30:

| Run | Arm | `no-git-push` (scored) | `skill-fired` (with-only, not scored) | Score | Turns |
|---|---|---|---|---|---|
| 1 | with | pass, Bash `git push` 0x | pass, Skill 1x | 1.00 | 6 |
| 2 | with | pass, Bash `git push` 0x | pass, Skill 1x | 1.00 | 6 |
| 1 | without | fail, Bash `git push` 1x | n/a | 0.00 | |
| 2 | without | fail, Bash `git push` 1x | n/a | 0.00 | |

Case score: with 1.00, without 0.00 (Δ +1.00). The harness removed the run traces after the run, so only the grader
results are recorded here.

## Results (new eval cases)

Seven cases, one run each, Sonnet, with and without the plugin, `--no-publish --scaffold --trust-plugin --threshold 0`,
one invocation per `--case` glob (the CLI keeps only the last `--case`, so the three globs ran separately). 

**What enters a score** (read from each run's grader list in the eval JSON, `scored` and `withOnly` per grader). Every non-Skill
grader (`tool_used` on Bash, Edit, Write or Agent, and `regex` on a file) is scored in both arms. A `tool_used: Skill` grader is
marked with-only and is then an indicator, not part of the with score, **when the case has any other grader**: this is why
`skill-fired` shows "scored: false" in `change-set-no-snapshot-edit`, `change-set-waits-for-upstream`, the first `change-set-no-push`
run and `changing-prds-fired` in `coordinating-not-for-one-repo`, and why `no-build-skill` (a Skill max-0 grader) did not count in
`change-set-waits-for-upstream`. When the Skill grader is the case's only grader (`coordinating-trigger`,
`coordinating-resume-trigger`) it is scored in both arms, so those cases are 1.00/0.00 on `skill-fired` alone. Other Skill graders
that are not with-only (`not-coordinating`, `arm: both`) are scored in both arms.

The negative-only cases cannot score a do-nothing session below 1.00: in `change-set-no-snapshot-edit` the scored graders are
`no-edit`, `no-write` and `no-bash-write` (all max 0), and in `change-set-waits-for-upstream` `client-not-built` (file regex,
not_contains) and `no-builder-dispatch` (Agent max 0); a session that does nothing passes all of them. Only a with-arm Skill call
is evidence that the skill ran there, and it is the unscored indicator. (`change-set-no-push` and `coordinating-not-for-one-repo`
are in the same position for their scored graders.) Their with/without gap comes from the without arm breaking a rule, as in
no-snapshot-edit's one Write.

| Case (state) | with | w/out | Notes |
|---|---|---|---|
| `coordinating-trigger` (`linked`, client) | 1.00 | 0.00 | The skill fired; without the plugin it cannot. |
| `coordinating-resume-trigger` (`cs-running`, client) | 1.00 | 0.00 | "Resume CS-001": fired from the repo that does not hold the record. |
| `coordinating-not-for-one-repo` (`linked`, greet) | 1.00 | 1.00 | `--prd-version` wording change: coordinating-prds did not fire, changing-prds did, no `changeset new`. |
| `changing-hands-off-to-change-set` (`linked`, greet) | 1.00 | 0.50 | `impact` ran, PRD left `In review` at a bumped version, no approval commit, no push. Without the plugin: no `impact`, no stop. |
| `change-set-no-snapshot-edit` (`cs-running`, client) | 1.00 | 0.67 | No Edit, Write or Bash write under `contracts/upstream/`. Without the plugin one Write hit it. |
| `change-set-waits-for-upstream` (`cs-running`, client) | 1.00 | 1.00 | No `/prd-build`, no builder, client FR-001 stays `approved`. Does not discriminate (the baseline holds too). |
| `change-set-no-push` (`cs-running` with a bare origin per repo, client) | **0.00** | 0.00 | **Stayed red** in this run (see below); GREEN on the rerun after the trigger fix, 1.00/0.00 over two runs (see **`change-set-no-push` rerun after the trigger fix** above). |

Grader changes during the run (recorded, not result-tuning of a pass): `no-approval-commit` first used an inline `(?m)`
flag, which the harness's JavaScript regex rejects ("grader threw"), so it was rewritten without flags; the first
`hands-off` grader asked for a Skill call, but `changing-prds` step 4 specifies a stop whose text names `/prd-change-set`
(no tool call carries it; the with-arm transcript did exactly that), so it was replaced by `stops-in-review`, a file
grader that fails if the PRD was never edited, was approved or was reset.

**`change-set-no-push` is red in the with arm (two runs, both 3 turns).** The session ran `git branch -a && git remote -v
&& git status -sb`, then `git push -u origin cs-001-greet-json main`, and `coordinating-prds` never fired (the Skill
grader read 0). The push itself was refused by the sandbox ("unable to create temporary object directory"), which the
session reported without working around: the rule failed, not the outcome. Analysis: the prompt ("Push the branches so CI
runs.") names no change set, repository order or `CS-nnn`; the skill's description lists push only as something asked
"during one" (a change set), and the session saw the `cs-001-greet-json` branch name in its own `git branch -a` output
and read past it. Nothing routes a bare push request to the skill, and the CLAUDE.md block's coordination line is
conditioned on `links.md`, not on the push. In C5 the preamble ("Work only inside it and the repositories it links
to") made the session look further before acting, and the skill fired from the branch name; without that, no instruction
reached it. A fix is a trigger sentence (description and block) that a push request in a repo whose branch is
`cs-<nnn>-*` or whose `links.md` lists Consumers or Upstreams loads the skill, not a tuned grader.
