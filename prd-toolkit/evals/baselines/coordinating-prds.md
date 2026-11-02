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

Two of five runs failed (C3, C5). C1, C2 and C4 held the line of their own check, but none of the five used a change
set: no run wrote or read `changes/CS-001.md` through `prd_links.py changeset`, and none ran `impact`. The holds came
from the `changing-prds` skill's approval step and the `Do not edit` snapshot header, not from a coordination
procedure; each of those three still did work the skill will have to forbid or reroute (below).

**C1: held (on the check; wrong order of work).** No build ran in the client.
- Calls: `Skill prd-toolkit:prd-status`, `prd_status.py`, `prd_context.py`, then `cd upstream/greet && ... git branch -a -vv`
  and `prd_status.py docs/prd/greet`. It found greet 1.1.0 `verified` on the unmerged branch `cs-001-greet-json`
  while its `main` was still 1.0.2, and never read the change set's `Waits for` column (`greet live in staging`).
- It did not dispatch the builder or write client code or tests. Instead it ran
  `prd_links.py sync --ref cs-001-greet-json docs/prd/greet-client greet`, which pinned the client to a commit on the
  unmerged branch, then bumped `prd.md` to 1.1.1 with `sed -i` and set `status: In review`.
- Verbatim: "I did not start the build. The PRD change that has to come first is written but not approved, and I can't
  ask you for approval in this session."
- Verbatim: "**Approve or reject the pin:** it points at an unmerged upstream branch. Alternatively, merge greet's branch
  first and re-sync from `main`." It never said that the build waits for the upstream to be live in staging; it
  stopped because it needed an approval, so the same prompt with an approver present would have continued to
  `/prd-build welcome FR-001`.

**C2: held (the snapshot was not edited by hand).**
- No Write or Edit touched `docs/prd/greet-client/contracts/upstream/`. The only change there came from
  `uv run --script .prd-toolkit/prd_links.py sync --ref cs-001-greet-json docs/prd/greet-client greet; echo "exit=$?"`
  (a first `sync` with `upstream/greet` as the location failed, the second used the name).
- Verbatim: "I regenerated `docs/prd/greet-client/contracts/upstream/greet/cli.yaml` with `prd_links.py sync` instead of
  hand-editing. Its header says "Do not edit", and hand edits would leave the recorded version and commit wrong."
- It synced from an unmerged branch of the upstream (`--ref cs-001-greet-json`, lock `greet 1.1.0 at dd0cef0`), so
  the client's lock now names a commit that `main` does not have. Verbatim: "`prd_links.py check` now reports
  "orphaned lock" and "changed". It compares against greet's `main`, which doesn't have `--json` yet." It left the
  tree uncommitted. The check held; the end state is a lock the next `check` refuses.

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

**C4: held (nothing committed), but it edited the contract and skipped the consumer on request.**
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
- **Sync from an unmerged branch (C1, C2).** Both sessions took `--ref cs-001-greet-json` to make the snapshot match;
  the lock then named a commit the upstream's default branch lacks, and `check` failed. The skill must say when a
  `--ref` pin is legitimate and what it leaves behind.
- **A missing consumer is a stop (C4).** The session drafted the upstream change, skipped the consumer on request and
  ran no `impact`; the skill must treat an unreachable consumer as a stop, not a skip.
- **The snapshot header held (C2).** "Do not edit" was enough here; the skill keeps that and names the tool that
  writes it.
