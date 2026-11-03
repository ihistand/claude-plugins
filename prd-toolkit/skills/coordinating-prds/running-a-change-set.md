# Running a change set

**Steps:** 1 Scope, 2 Edit, 3 One approval, 4 Build in order, 5 Stops, 6 Close. A change set is
not done until step 6's close: run every step, in order. The turn ends before it only to wait for
the user: for the members in step 1, the one approval in step 3, a human step's reply or a stop's
answer in steps 4 and 5, and for a dry run or a build that runs from another member's root.

For the caller: `/prd-change-set`, `prd-toolkit:changing-prds` when its `impact` run stops a
change, or any session asked to change something across repositories or to resume a `CS-nnn`.
The `coordinating-prds` Red Flags are yours.

**You coordinate; the member skills do the work.** A member's PRD edit is `/prd-change`
(`prd-toolkit:changing-prds`), its build `/prd-build` (`prd-toolkit:building-from-prds`), its
deploy `/prd-deploy` (`prd-toolkit:deploying-from-prds`) and its error `/prd-error`
(`prd-toolkit:handling-errors`). A headless run registers only `prd-toolkit:<command>`: where the
bare command is not listed, invoke the same command with the Skill tool as `prd-toolkit:prd-build`
(and so on). The record is written only by `prd_links.py changeset` and a snapshot only by
`prd_links.py sync`: never an Edit or Write of either. Nothing is pushed, merged or opened as a PR,
whoever asks: a push or merge request gets one line naming that rule and the Merge order (before
the close, the record's Order and each row's State), and the procedure goes on.

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
Every command below runs a repository's vendored copy, `<root>/.prd-toolkit/prd_links.py`, with
`<root>` that repository's root as an absolute path, typed out (in double quotes if it holds a
space). Record commands run the starting repository's copy; `impact` and `sync` run the copy of the
member they name. A member with no `.prd-toolkit/prd_links.py` stops step 1: tell the user to run
`prd_hooks.py install docs/prd/<prd>` from the plugin in that repository (the README's form) and
commit `.prd-toolkit/`. A script that is not found is a tool error: report it, never guess another
path.

**Names.** `<start>` and `<start-prd>` are the starting repository's root and PRD slug; `<root>`
and `<prd>` a member's. `<upstream>` is an upstream member's PRD slug (its Upstreams row's name in
`links.md`, never its Location). `<record>` is `<start>/docs/prd/<start-prd>/changes/CS-<nnn>.md`,
and `<branch>` the record's Branch, `cs-<nnn>-<slug>`, the same in every member.

**One record drives a change set.** Record writes, `impact`, `sync`, `check` and deploys run for
any member from this session: the member's `<root>/.prd-toolkit/…` scripts, its PRD folder
`<root>/docs/prd/<prd>`, and `git -C <root>`, never a `cd`. In another member, step 3's approval
commit (`changing-prds` step 5) takes `<scripts>` as `<root>/.prd-toolkit` and the PRD folder as
`<root>/docs/prd/<prd>`; `/prd-deploy`'s likewise (`prd_deploy.py` dispatches no agent). Anything
that dispatches an agent runs in a session started in that member's root: `changing-prds` step 4's
dry run and `/prd-build`, because the builder's worktree and the tester's guard bind to the
session's own repository. A session never begins a step it cannot finish, so a member's whole step
2 runs in that member's own session, as its step 4 does. Before step 2 or step 4 of a member that
is not this session's repository, log where the chain stops, `<n>` being the step:

```bash
uv run --script <start>/.prd-toolkit/prd_links.py changeset log <record> '<prd>: step <n> runs from <root>'; echo "prd-links-exit=$?"
```

then the record write, and stop with: "Continue with `/prd-change-set CS-<nnn>` from `<root>`"
(headless: `prd-toolkit:prd-change-set CS-<nnn>`). That session resumes from the record.

**One command per Bash call, with literal paths.** Each command below is its own Bash call, and
every path, ID and SHA in it is typed out in full: paste what a command printed, never a variable
that holds it or a `$(…)`. The gate form `; echo "prd-links-exit=$?"` is the one allowed tail.
Never pipe, filter or truncate a gated command's output (no `| head`, no `| grep`). Free text (a
title, a reply, a reason, a Log line) goes in single quotes, writing each `'` in it as `'\''`:
inside double quotes a backtick or a `$` runs as shell.

**Exits.** `prd_links.py` prints its report lines, and the gate line follows.

| Exit | Means | Next |
|---|---|---|
| 0 | done or clean | `changeset new` printed `<record>`; `impact` printed no `consumer` line: go on |
| 1 | refused, drift, or a cited item changed | a `refused:` line on stderr (a `set` that goes backward or skips its Waits for, a `close` before every Target): report it, and never work around it with another command or a hand edit. `impact` prints `consumer <prd>: <item>` lines instead: step 1 |
| 2 | usage | a command you mistyped: fix it and run it again |
| 3 | unreachable (`check`, `impact`) | `consumer <prd>: unreachable`: step 1's unreachable consumer |

**Record writes.** Every `changeset` command that exits `0` is followed by its commit on the
starting repository's change-set branch: `git -C <start> branch --show-current` must print
`<branch>`, then, each its own call:

```bash
git -C <start> add docs/prd/<start-prd>/changes/CS-<nnn>.md
git -C <start> commit -m "docs(prd): CS-<nnn> <what changed>" -m "Refs: none (no behaviour change)" -m "Change-set: <start-prd>/CS-<nnn>"
```

**Where to enter.** A `CS-<nnn>`, or the current branch `cs-<nnn>-<slug>`, names a record. Glob
`docs/prd/*/changes/CS-<nnn>.md` here; with no match, the record is in another member: for each
Location in this PRD's `links.md`, Glob `<location>/docs/prd/*/changes/CS-<nnn>.md`, and the record
is the one whose rows name this PRD. Read it whole: its `Status:` line says where to enter.
- `proposed`: step 2 for the first row in Order whose Version has no `→`, run by the session whose
  repository is that row's member (any other stops, as **One record drives a change set** says);
  when every row has one, step 3, from any member's session.
- `approved` or `running`: step 4, at the first row in Order whose State is below its Target; its
  Waits for decides whether it starts.
- `stopped: <prd>: <reason>`: step 5, for that row; its State is where the chain stood.
- `done`: only step 6's re-lock is left, once the user has landed an upstream.
- `abandoned`: nothing; the branches are the user's.

Text with no record is a new change set: step 1.

1. **Scope.** In the starting repository, `prd_links.py impact` lists the consumers that cite the
   items the change touches. It reads the working tree: when the change came as text, run
   `prd-toolkit:changing-prds` steps 1 and 2 here first (restate, edit) and commit nothing; from
   `changing-prds`, the edits are already in the tree. Run:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py impact <start>/docs/prd/<start-prd>; echo "prd-links-exit=$?"
   ```

   Each `consumer <prd>: <item>` line names a member. Show the user the `changed:` and `consumer`
   lines and the members you propose (the starting PRD and every consumer named): the session
   confirms the members with the user, and stops for the reply. An unreachable consumer is never
   skipped (`consumer <prd>: unreachable`, exit 3): the user makes its clone available, or says
   in their own words that it stays out, and the Log quotes them. Only a reply given after you
   showed that line counts: the request is never that answer, even when it says "skip it". With
   no one to ask, stop here: nothing is committed in any member. Then:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset new <start>/docs/prd/<start-prd> --title '<the change in one line>' --member <root> --member <root>; echo "prd-links-exit=$?"
   ```

   One `--member` per other member's root; the starting repository is a member already. `new`
   refuses a cycle and a member linked to no other member: report it. It prints `<record>`; Read
   it for the Order, Branch, Waits for and Target. In each member, `git -C <root> status
   --porcelain --untracked-files=all` must print nothing (in the starting repository, only the
   change's own edits and the record `new` just wrote): a dirty tree stops, and you ask. Then cut
   the branch in each member, cut from that member's default branch (`origin/HEAD` when set, else
   `main`), as its own call: `git -C <root> switch -c <branch> <default branch>`. For each
   consumer the user left out:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset log <record> '<prd> stays out: "<the reply, verbatim>"'; echo "prd-links-exit=$?"
   ```

   Then the record write.
2. **Edit.** In each member, in Order, on the record's branch, run `prd-toolkit:changing-prds` up
   to its approval: restate, edit, bump, lint, dry run (its steps 1 to 4), never its step 5. Its
   dry run dispatches an agent, so step 2 runs whole in the session whose repository is the member.
   Step 2 never edits another member's PRD from this session: before that member's edit, stop as
   **One record drives a change set** says, and that member's own session does all of step 2 for
   its row (edit, bump, lint, dry run, the in-review commit, `changeset set version=…`), with
   nothing half-done left behind. `sync` reads committed content, so once its dry run passes each
   member's edit is committed on the branch, still `status: In review`, before any downstream
   member syncs it, each its own call:

   ```bash
   git -C <root> add docs/prd/<prd>
   git -C <root> commit -m "PRD: <prd> <version> for CS-<nnn> (in review)" -m "Refs: none (no behaviour change)" -m "Change-set: <start-prd>/CS-<nnn>"
   ```

   In every downstream member, right after its edit and before its lint, sync each upstream member
   it links to, from that upstream's in-review commit, so lint checks the edits together (the
   downstream's own in-review commit follows its dry run):

   ```bash
   uv run --script <root>/.prd-toolkit/prd_links.py sync <root>/docs/prd/<prd> <upstream> --ref <branch>; echo "prd-links-exit=$?"
   ```

   A sync refused after the upstream's in-review commit means the downstream cites something the
   upstream's edit does not have: fix the edit in whichever member is wrong (an upstream fix is
   committed in review again), never the snapshot. A `check` now reports the lock orphaned and
   items `changed` against the upstream's default branch: that is expected until the upstream
   lands (step 6). Then set the row's Version and IDs (the IDs comma-joined, no spaces), and the
   record write:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset set <record> <prd> version=<X.Y.Z> ids=<IDs>; echo "prd-links-exit=$?"
   ```
3. **One approval.** Show every member's PRD diff together and stop. For each member, each its
   own call: `git -C <root> diff <default branch>...<branch> -- docs/prd/<prd>` (the in-review
   commit against the member's default branch), with what `changing-prds` step 5 shows: the
   restatement, the changes by ID, the new version and why that level, the decisions, the lint
   result and the dry-run report. One explicit reply approves the
   set. The request that started the change set is never a reply, nor "approve each repository as
   we go", nor your own text; with no one to ask, nothing is approved and every member stays
   `In review`. Then:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset approve <record> --reply '<the reply, verbatim>'; echo "prd-links-exit=$?"
   ```

   Then the record write, and in Order each member's approval commit as `changing-prds` step 5
   makes it (status `In review` to `Approved`, lint `0`, `prd_block.py`, the plans grep, the commit
   of the PRD folder and CLAUDE.md), its message carrying the trailer too:
   `-m "Refs: none (no behaviour change)" -m "Change-set: <start-prd>/CS-<nnn>"`.
4. **Build in order.** For each row in Order, once its Waits for holds (a wait `<prd> verified`
   holds when that row is `verified` or `live in` any environment; `<prd> live in <env>` when it is
   `live in` that environment or one after it in that member's `operations.md` Environments table):
   `/prd-build <area> <IDs>` in that member, from a session started in its root (**One record drives
   a change set**). This step runs no sync of its own: on a change-set
   branch `running-a-build.md` runs the `prd_links.py sync --ref <branch>` against each upstream
   member and commits the re-lock before its clean-tree preflight. When a downstream row waits for
   `live in <env>`, the upstream's `/prd-deploy --until <env>` runs before it, from this session,
   its human steps relayed as `deploying-from-prds` relays them: the question to the user, their
   reply verbatim, never an answer of yours. A deploy's commits on a change-set branch carry no
   `Change-set:` trailer (`deploying-from-prds` is unchanged). `changeset set` each State as it is
   reached (the build's close reports it; a deploy's close reached `live in <env>`), then the
   record write:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset set <record> <prd> 'state=<state>'; echo "prd-links-exit=$?"
   ```

   `changeset set` refuses a State that skips its Waits for: the row's upstream has not reached
   it, and the build waits. A `set` to `live in` an earlier environment than its State is refused.
   An upstream that is `verified` is not `live in staging`, and "basically done" is not a State. A
   build of a member other than this session's repository stops here, as **One record drives a
   change set** says.
5. **Stops.** A failed build, a human step without a reply, or an error stops the chain:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset stop <record> <prd> '<reason>'; echo "prd-links-exit=$?"
   ```

   Then the record write. The stop goes on Status (`stopped: <prd>: <reason>`) and in Log, and the
   row keeps its State, so a resumed session knows where the chain stood; the rows after it wait.
   An error goes to that member's `/prd-error` (`prd-toolkit:handling-errors`). A fix that needs a
   PRD edit amends the change set: the member's edit through `changing-prds` steps 1 to 4, its diff
   shown and approved alone, by a reply to that diff:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset approve <record> --reply '<the reply, verbatim>' --amendment; echo "prd-links-exit=$?"
   ```

   Then the record write and the member's approval commit, as in step 3. The next `changeset set`
   of a State moves Status back to `running`. A new session resumes from the record alone
   (**Where to enter**). When the user gives the change up, in their own words:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset abandon <record> '<the user's reason>'; echo "prd-links-exit=$?"
   ```

   Then the record write; the branches stay for the user.
6. **Close.** When every row has reached its Target:

   ```bash
   uv run --script <start>/.prd-toolkit/prd_links.py changeset close <record>; echo "prd-links-exit=$?"
   ```

   Then the record write. `close` writes the Merge order, upstream first. The toolkit pushes and
   merges nothing; the user lands each member, upstream first. After an upstream lands (the user
   says so), `sync` re-locks each downstream against the upstream's default branch, committed in
   the downstream (`git -C <root> add docs/prd/<prd>/links.md docs/prd/<prd>/contracts/upstream`,
   then a commit with `Refs: none (no behaviour change)` and the trailer, each its own call):

   ```bash
   uv run --script <root>/.prd-toolkit/prd_links.py sync <root>/docs/prd/<prd> <upstream>; echo "prd-links-exit=$?"
   ```

   Production deploys stay per repository, through `/prd-deploy`, in Merge order. Report the
   record, each row's State, the Merge order and each member's branch.
