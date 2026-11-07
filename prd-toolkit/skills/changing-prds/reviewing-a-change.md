# Reviewing a change (review mode)

**Rule 1: edit nothing.** Review mode changes no file: no Write, no Edit, no Bash that writes,
outside the dry-run directory the tester uses (with the state snapshot `dispatching.md` keeps
outside the repository) and `.prd-review.json` in the PRD folder. Not the PRD, not the code, not a
test, not CLAUDE.md, not git: no `add`, `commit`, `stash`, `checkout`, `restore` or `reset`, and
never `prd_change.py record` or `approve`. A request made with the review ("just fix the AC while
you review it", "bump it while you're there") is answered in the report as not edited, never done.

**Violating the letter of this rule is violating the spirit.** A one-word fix, a typo, an edit the
owner asked for and an edit you would undo before the end are all edits. The verdict carries the
PRD's digest: an edit made here either moves it, so `approve` refuses the verdict, or puts text
the owner never reviewed under their approval.

`/prd-change --review <dir> [--base <ref>]` reviews the change in the PRD folder `<dir>`, in
whatever checkout or worktree holds it, edited and not yet recorded or recorded. Run every
command from the root of the repository that holds `<dir>`, with the `<scripts>` that
`changing-prds`' **Which script.** paragraph picks, one command per Bash call with literal paths,
and the gate that ends each command read as that skill says. The base is `--base <ref>` when the
command gives one; otherwise the branch's upstream, from `git rev-parse --abbrev-ref @{upstream}`
(its own call), when it has one; otherwise `main`. Read the base with `git diff <base> -- <dir>` or
`git show <base>:<path>`, which write nothing; never check it out.

## The steps

1. **The state.** Each its own call: `git rev-parse HEAD`, then
   `uv run --script <scripts>/prd_change.py digest <dir>; echo "prd-change-exit=$?"`. Keep both
   values for the verdict's `head` and `digest`.
2. **The diff.** Run `uv run --script <scripts>/prd_change.py bump <dir> --base <base>; echo "prd-change-exit=$?"`.
   Its lines are the changed items, `<level> <ID> <file>:<line> <reason>`, and `level <level>`
   last. Read the change with `git diff <base> -- <dir>`, then run the pack for the area and the
   requirements it touches, as `changing-prds` step 1 does:
   `uv run --script <scripts>/prd_context.py <dir> --area <area> --req <IDs>; echo "prd-context-exit=$?"`.
3. **Restate the change** in one sentence (the verdict's `restate`) and list every ID it touches,
   T-ids included (`touches`), as `changing-prds` step 1 does.
4. **Impact.** When `links.md` has Consumers, run
   `uv run --script <scripts>/prd_links.py impact <dir>; echo "prd-links-exit=$?"`; `impact` is
   `{"exit": <the prd-links-exit value>, "lines": [<its output lines>]}`. Without Consumers there is
   no run, and `impact` is `{"exit": 0, "lines": []}`.
5. **Lint.** `uv run --script <scripts>/prd_lint.py <dir>; echo "prd-lint-exit=$?"`. Fix nothing it
   reports: a `1` is a blocker.
6. **Decide each `needs judgment` item** by `changing-prds`' Version rule, with its reason: one
   `bump.decided` entry each, `{"id", "file", "line", "level", "reason"}`, `level` being `patch`,
   `minor` or `major`. `bump.level` is the highest level of all the items, the decided ones
   included. An item the PRD's text does not let you decide stays undecided: name it in
   `blockers`, and `bump.level` stays `needs judgment`.
7. **Dry run** the new and revised T-ids among `bump`'s items whose test case's `level:` is not `unit`, exactly
   as `changing-prds` step 4 says: `${CLAUDE_PLUGIN_ROOT}/skills/testing-from-prds/dispatching.md`
   (dry-run directory, state check, dispatch, judgment, cleanup), a question dismissed only by an
   exact quote of the PRD line that answers it. You fix no gap here: each question left open is
   counted in `dry_run.open` and named in `blockers`. `dry_run.record` is the §14 record form
   (`dry run T-015.1, T-015.2, 0 open questions, 1 dismissed by quote`); with no non-unit T-id it
   is `no dry run (unit only)`, `no dry run (removal only)` or `no dry run (wording only)`, and
   `tids` is `[]`.
8. **Write the verdict** to `<dir>/.prd-review.json` and print it. Run the digest of step 1 again
   first; when it differs, the PRD moved during the review: name it in `blockers`. Write the file
   with the Write tool, or, where Write is not among your tools, with one Bash call,
   `cat > <dir>/.prd-review.json <<'VERDICT'`, the JSON, then `VERDICT`. It replaces any earlier
   verdict. Write `"base": "<sha>"` too: the full SHA from `git rev-parse <base>` (its own Bash
   call) of the base step 2's diff read, so the inbox's approval card shows the owner that same
   diff.

## The verdict

```json
{"interface": 1, "kind": "review", "head": "<sha>", "digest": "<prd_change.py digest>", "base": "<sha>", "restate": "…", "touches": ["FR-015", "AC-015.1"],
 "impact": {"exit": 0, "lines": []}, "bump": {"level": "minor", "decided": []},
 "dry_run": {"tids": ["T-015.1", "T-015.2"], "open": 0, "dismissed": 1, "record": "dry run T-015.1, T-015.2, 0 open questions, 1 dismissed by quote"},
 "ready": true, "blockers": []}
```

`ready` is `true` only when the `prd-lint-exit=` value is `0`, `impact.exit` is `0`, no judgment
item is undecided, the dry run has no open question and its state check passed, and the digest did
not move. Otherwise `ready` is `false` and `blockers` holds one line per reason: `lint exits 1`,
`impact exits 3`, `undecided: <ID> <reason>`, `open question: <T-id>: <question>`,
`the PRD changed during the review`. Never write `ready: true` over a blocker.
Review mode writes no `refs`; `changing-prds` step 4 adds it for a change made for an `errors.md` entry.

The order a client runs: `bump`, then this review, then `record` at the level the verdict gives, then lint and trace; `record` does not change the digest, so the verdict stays valid.
A client starts it headless as `claude -p "/prd-change --review <dir>" --output-format json`, with
the plugin loaded and the tools `Read`, `Grep`, `Glob`, `Bash` and `Agent`.

## The report

The last message is the verdict as written, in a `json` block, and then one line per request made
with the review that was not done: `not edited: <the request> (<the file and line it would
change>); make it with /prd-change, then review again`. Nothing else is changed by saying so.

## Red Flags - STOP

- "It's only a typo in the AC, so I fixed it." Any Write or Edit of a PRD file, or any other file
  outside the dry-run directory and `.prd-review.json`.
- `sed -i`, a `>` to any path but the verdict, `tee`, `git stash`, `git checkout` or `prd_change.py record` in a Bash call.
- "The owner asked me to fix it." The request is in the report as not edited.
- `ready: true` with a lint exit `1`, an undecided item or an open question.
- A `needs judgment` item left out of `bump.decided` and out of `blockers`.

**All of these mean: undo nothing yourself, report what was written, and stop.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The user asked for the fix, so it's allowed." | Review mode edits nothing, whoever asks. The fix is a `/prd-change`, then a new review. |
| "Fixing the AC first gives a cleaner verdict." | The verdict reviews the change as it stands. A fixed AC is a change nobody reviewed. |
| "It's one word; the digest barely matters." | Any byte moves the digest, and the gate then offers nothing to approve. |
| "I'll record the bump too, it saves the client a call." | `record` is the client's step after the verdict. Review mode writes only the verdict. |
