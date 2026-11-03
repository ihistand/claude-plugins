# prd-toolkit 0.7: PRDs across repositories — design

> **Date:** 2026-11-02
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and the 0.2 to 0.6 addenda
> (`2026-11-01-prd-toolkit-0.6-design.md` last). Where this addendum and any of them disagree, this
> addendum wins for 0.7.

> **Revisions.**
> - §6 (plan): a stop is recorded on Status (`stopped: <prd>: <reason>`) and in Log; the row keeps its State, so a resumed session knows where the chain stood. `changeset set` of any State moves Status back to `running`. State is never `stopped:`.
> - §4 (plan): a custom type's snapshot file names its type, and `schema.sql` names its dialect, in the header (` Type: <kind>.`, ` Dialect: <dialect>.`), because the downstream PRD declares neither.
> - §8 (plan): `check --ci` exits 0 where `check` would exit 3, after printing the unreachable line, so the generated job passes; the generated CI line runs `check --ci`.
> - §4 (plan): a target or `Traces:` token `<kind>:<a>/<b>` is prefixed when `<a>` matches `[a-z][a-z0-9-]*` and `<kind>` is not `code`; a prose span `` `<a>/<t>.<c>` `` is prefixed only when `<a>` is an Upstreams name, so a path such as `src/importer.py` stays prose.
> - §3 (plan): an empty Needs means `live in` the Environment of the first `deploy`-gate level in `testing.md` Levels order; with none, `verified`.
> - §6 (plan): when two downstream members need different `live in` environments of one upstream, its Target is the one later in the upstream's `operations.md` Environments table.
> - §5 (plan): `check`'s Consumers side reads each consumer at its default branch; `--ref` applies to the Upstreams side only.
> - §4, §15 (execution, R-2a): asyncapi channels and operations are not citable across repositories in 0.7. §4's table covers `events.md` sections only, so `sync` refuses with `<kind>:<name>: asyncapi items cannot be cited across repositories`, and §15 lists it.
> - §8 (execution, R-8a): `/prd-status` runs the link check for path locations only. A git URL location shows `check: not run (git URL; run prd_links.py check)`, which keeps status fast and offline. CI, the deploy pre-flight and `prd_links.py check` do the full check.
> - §8 (execution, R-8b): `/prd-status` shows the verdict counts (`check: same 3`) in place of "the last `check` line", because counts carry more than one line.
> - §4 (execution, R-10b): an upstream's custom contract type is citable without the downstream declaring it; a prefixed reference of any kind that is not a built-in target kind counts as a citation, and `upstream-refs` resolves it against the snapshot through the header's `Type:`. A prefixed `component:` or `page:` target gets `kind '<kind>' does not cross repositories`.
> - §4, §14 (execution, R-10c): prefix handling (citations, `upstream-refs`, `snapshot-cited` and the prefixed skips in `test-refs`, `schema-refs` and sufficiency) applies only in a PRD that has `links.md`, so a PRD without it needs no edit (§14).
> - §6 (execution, R-11b): each upstream member's PRD edit is committed on the change-set branch with status `In review` (`Refs: none`, the `Change-set:` trailer) before a downstream member syncs, because `sync` reads commits, never working trees. Step 3's approval commit flips it to `Approved`.
> - §6, §15, §13 Q2 (execution, R-11c): one record drives a change set. Record writes, `impact`, `sync`, `check` and deploys run for any member from any session. A dry run and a build dispatch agents whose worktree and guard bind to the session's own repository, so they run in a session started in that member's root. This revises §6's "one session drives it all", §15's "One session drives a change set", and Q2's pass line, which now allows a resume per member.
> - §9 (execution, R-11d): `prd-builder` carries the `Change-set:` trailer on its commits when the dispatch passes one.
> - §6 (execution, R-11e): a session never begins a member's step 2 that it cannot finish. For a member that is not the session's repository it logs the stop and stops before editing, and that member's own session runs the whole of step 2 for its row.

## 1. Scope

Until 0.6 a PRD stands alone: every reference resolves inside its own folder, and a change, a build
and a deploy run in one repository. A real system is a chain of repositories (a source feeds a
transform, which feeds a reporting layer), and a field added upstream must reach the repositories
that use it. 0.7 **links PRDs across repositories**: a downstream PRD cites an upstream PRD's
contract items, lint and CI catch a cited item that changed or disappeared, and one coordinated
change edits every affected PRD with one approval, then builds (and, where a link needs it,
deploys) each repository in dependency order. 0.3's one-PRD-per-repository rule stands.

0.7 delivers:
- `links.md`, a PRD's Upstreams and Consumers tables, with the lock of every upstream (section 3);
- cross-PRD references `<kind>:<prd>/<name>` and the snapshot `contracts/upstream/<prd>/` (section 4);
- `prd_links.py` (`add`, `sync`, `check`, `impact`, `changeset`) (section 5);
- change sets: the record `changes/CS-nnn.md` and the `coordinating-prds` skill with its procedure
  `running-a-change-set.md` and `/prd-change-set` (sections 6 and 9);
- four lint rules (32 → 36), the `Change-set:` trailer in the trace and the hook (section 7);
- links and change sets in `/prd-status`, context packs, the generated CI and deploy pre-flight
  (section 8);
- 0.5's F-a (the interview asks about packaging) and O-a (bare slash commands in headless runs)
  (section 10).

It is **proven by** slice 4 of the hello-world project: a second repository, `greet-client`, that
uses `greet` (section 13).

### Decisions

| Decision | Choice |
|---|---|
| Goal | **Coordinate the change**, which includes catching breakage: one approval for every affected PRD, one build per repository in dependency order |
| How a downstream PRD reaches an upstream | **A pinned snapshot, like a lockfile.** `links.md` names each upstream's location (a path or a git URL) and its lock (version and commit); `contracts/upstream/<prd>/` holds only the cited items. Lint and trace read the snapshot only, so every repository checks offline |
| What a downstream build waits for | **Declared per link:** `needs: verified` or `needs: live in <env>`. An empty Needs means `live in` the environment of the downstream's own deploy-gate tests |
| Where a change set lives | **In the repository where it starts**, as `docs/prd/<name>/changes/CS-nnn.md`; the other repositories' commits carry a `Change-set:` trailer that points to it |
| How an upstream finds its consumers | **The upstream lists them** in its own `links.md`; `prd_links.py check` fails when the two sides disagree, and `impact` reads each consumer's snapshot |
| Shape | **A new script and skill; the existing skills stay single-repository.** `prd_links.py` owns links, snapshots and the change-set record (its only writer); `coordinating-prds` calls `/prd-change`, `/prd-build` and `/prd-deploy` per repository |
| Extras | 0.5's F-a and O-a. Nightly drift and smoke, `prd-error` issues and schema drift stay deferred |
| Release vehicle | Branch `feat/prd-toolkit-0.7`, cut from `main` at `b7b75a9`; version 0.7.0 in `plugin.json`, `marketplace.json` and `web/src/data/plugins.js` |

## 2. Components

| Path (under `prd-toolkit/`) | New or changed | Role |
|---|---|---|
| `scripts/prd_links.py`, `scripts/prdlint/links.py` | new | The link, snapshot and change-set commands (sections 5 and 6) |
| `scripts/prdlint/snapshot.py` | new | Item extraction per contract kind, shared by `sync`, `check`, `impact` and lint |
| `skills/coordinating-prds/SKILL.md` | new | When a change crosses repositories, the rules and red flags; its first instruction is to Read `running-a-change-set.md` whole |
| `skills/coordinating-prds/running-a-change-set.md` | new | The caller procedure (section 6) |
| `commands/prd-change-set.md` | new | `/prd-change-set [<CS-nnn> \| <text>]` |
| `scripts/prdlint/model.py` | changed | Parses `links.md`, the `<prd>/` prefix and `changes/CS-nnn.md` |
| `scripts/prdlint/rules/` | changed | `links-format`, `upstream-refs`, `snapshot-cited`, `change-sets` (36 rules); `test-refs` and `schema-refs` resolve the prefix |
| `scripts/prdlint/trace.py`, `scripts/prd_git_hook.py` | changed | The `Change-set:` trailer (section 7) |
| `scripts/prdlint/hooks.py` | changed | Vendors `prd_links.py`; the generated `prd-lint` job runs `prd_links.py check` |
| `scripts/prdlint/status.py`, `scripts/prd_context.py` | changed | Links and change sets; snapshot items in a pack |
| `scripts/prdlint/deploy.py` | changed | Deploy pre-flight runs the link check (section 8) |
| `skills/changing-prds/SKILL.md` | changed | The `impact` step and the hand-off (section 9) |
| `skills/building-from-prds/running-a-build.md` | changed | A build on a change-set branch (section 9) |
| `skills/authoring-prds/SKILL.md`, `skills/adopting-prds/SKILL.md` | changed | Propose links; F-a |
| `references/prd-format.md`, `references/clarify-categories.md`, `references/quality-checklist.md` | changed | `links.md`, the prefix, the snapshot, the record; packaging |
| `templates/claude-block.md`, `README.md` | changed | The coordination role; Links and Change sets; O-a; the upgrade note |

## 3. `links.md`

An optional file in the PRD folder, beside `prd.md` and `adoption.md`. With no `links.md` a PRD has
no links, and nothing in this addendum applies to it.

```
# Links

## Upstreams

| Upstream | Location | Version | Commit | Needs |
|---|---|---|---|---|
| greet | `../greet` | 1.1.0 | 4f1c9a2 | live in staging |

## Consumers

| Consumer | Location |
|---|---|
| dashboards | `git@example.com:org/bi.git#docs/prd/dashboards` |
```

- **Upstream / Consumer:** the other PRD's `prd:` slug. Unique within its table.
- **Location:** a backticked path to the other repository's root, relative to this repository's
  root, or a git URL followed by `#<PRD folder>`. A path location's PRD folder is found as
  `docs/prd/<slug>`; a URL location names it.
- **Version / Commit:** the lock. The upstream PRD's `version:` and the upstream repository commit
  (7 to 40 hex digits) the snapshot was copied from. Only `prd_links.py sync` writes them.
- **Needs:** `verified`, or `live in <env>` with `<env>` an environment of the upstream's
  `operations.md`. Empty means `live in` the Environment of the first `deploy`-gate level in `testing.md` Levels
  order; with no deploy-gate level, empty means `verified`.

Adding `links.md` to a PRD is a patch, recorded as the §14 row `format: links.md (prd-toolkit 0.7)`,
as 0.4's Gate column was. Adding or removing a link is part of a PRD change and follows its bump.

## 4. References and the snapshot

**The prefix.** A reference to an upstream item puts the upstream's slug and a `/` before the name:

| Where | Form | Example |
|---|---|---|
| test case `target:` | `<kind>:<prd>/<name>` | `cli:greet/greet`, `table:transform/orders_daily`, `op:orders/createOrder` |
| prose (`schema-refs`) | `` `<prd>/<table>.<column>` `` | `` `transform/orders_daily.amount` `` |
| `Traces:` | the target form | `Traces: UJ-01; cli:greet/greet` |

A target or `Traces:` token `<kind>:<a>/<b>` is prefixed when `<a>` matches `[a-z][a-z0-9-]*` and
`<kind>` is not `code`. A prose span `` `<a>/<t>.<c>` `` is prefixed only when `<a>` is an Upstreams
name, so a path such as `src/importer.py` stays prose. Prefix handling applies only in a PRD that
has `links.md`.

The kinds that cross are `op`, `table`, `event`, `job` and a custom type whose files are YAML
mappings (as `test-refs` already resolves them). The downstream does not declare an upstream's
custom type; the snapshot header names it. A prefixed `component:` or `page:` target is refused:
`kind '<kind>' does not cross repositories`. `code:` never crosses: a unit target belongs to
its own repository. A downstream test of an upstream item runs against the upstream's deployed
environment or a fixture, never the upstream's source.

**The snapshot.** `contracts/upstream/<prd>/` holds the cited items only, copied verbatim, in files
named as in the upstream's `contracts/`:

| Kind | What is copied |
|---|---|
| `table` | the `CREATE TABLE` statement and its `COMMENT ON` lines, into `schema.sql`; `--` comment lines directly above the statement travel with it, `/* */` ones do not |
| `op` | the operation under its path, every `components` entry it `$ref`s, transitively, and the `info` block, into `openapi.yaml` |
| `event`, `job` | the `### <name>` section, heading to the next heading of the same level, into `events.md`; an item of `contracts/asyncapi.yaml` cannot be cited across repositories |
| custom YAML type | the cited top-level keys, into the type's file |

Each snapshot file starts with one comment line in its own syntax (`-- ` for `.sql`, `# ` for
`.yaml`, `<!-- … -->` for `.md`):
`Snapshot of <prd> <version> at <commit>, written by prd_links.py sync. Do not edit.` A custom
type's file adds ` Type: <kind>.` and `schema.sql` adds ` Dialect: <dialect>.`, because the downstream
declares neither. An uncited
item never reaches the snapshot, so a private upstream's other contracts stay out of a downstream
repository that may be public.

Lint, trace, the tester and context packs read the snapshot, never the upstream. `contracts-valid`
skips `contracts/upstream/` (the upstream validates its own contracts; `check` proves the copy is
faithful), and no §7 Contract types glob matches inside it.

## 5. `prd_links.py`

Every command takes the PRD folder first. Exit 2 is a usage error throughout.

| Command | Does | Exits |
|---|---|---|
| `add <PRD> <location> [--needs <value>]` | Reads the other PRD's slug at the location; writes the Upstreams row here (lock empty) and the Consumers row in the upstream's `links.md` when its clone is a path on disk; otherwise prints the Consumers row for the user to add there | 0; 1 when the row exists or the location has no PRD |
| `sync <PRD> <upstream> [--ref <ref>]` | Collects every `<upstream>/` reference in this PRD, copies those items from the upstream at `<ref>` (default: the upstream's default branch), rewrites the snapshot files and the lock | 0; 1 when a cited item is not in the upstream, naming it, and nothing is written |
| `check <PRD> [--ref <ref>]` | For each Upstream: compares every snapshot item with the upstream at `<ref>` (`same`, `changed`, `removed`), says `newer than lock` when the upstream's version is higher, and flags a lock commit that is not on the upstream's default branch. For each Consumer: reads its snapshot of this PRD and compares it the same way. Both sides: each Upstreams row has the matching Consumers row on the other side, and back | 0 clean; 1 drift (any `changed`, `removed`, an orphaned lock, a missing row on either side); 3 when nothing drifted but a side was unreachable, naming it |
| `impact <PRD> [--base <ref>]` | Lists the contract items this PRD's working tree changes against `<base>` (default `HEAD`), and for each Consumer the cited ones among them | 0 none cited; 1 a consumer cites a changed item; 3 a consumer was unreachable |
| `changeset …` | The record's only writer (section 6) | |

`check --ci` exits 0 where `check` would exit 3, after printing the unreachable line. The Consumers
side reads each consumer at its default branch; `--ref` applies to the Upstreams side only.
`newer than lock` alone is a note, not drift. The upstream's default branch is `origin/HEAD` when it
is set, else `main`. A git URL location is fetched with the user's own git credentials into
`${XDG_CACHE_HOME:-~/.cache}/prd-toolkit/links/<hash of the URL>` (a partial clone, read with
`git show <ref>:<path>`); nothing is written under `.git/` or inside a repository. A location the
script cannot read or fetch is unreachable.

## 6. Change sets

### The record

A change set has the ID `CS-nnn`, numbered per PRD and never reused. Its record is
`docs/prd/<name>/changes/CS-nnn.md` in the repository where it starts, and `prd_links.py changeset`
is its only writer.

```
# CS-001 Show the greeting as JSON in the client

Started: 2026-11-03 in greet
Status: running
Approval: 2026-11-03, "<the user's reply, quoted>"

| Order | PRD | Location | Branch | Version | IDs | Waits for | Target | State |
|---|---|---|---|---|---|---|---|---|
| 1 | greet | `.` | cs-001-json-greeting | 1.1.0 → 1.2.0 | FR-003 | — | live in staging | live in staging |
| 2 | greet-client | `../greet-client` | cs-001-json-greeting | 1.0.0 → 1.1.0 | FR-002 | greet live in staging | verified | approved |

## Log

- 2026-11-03 greet built and verified (Refs: FR-003)
- 2026-11-03 greet deployed to staging, run 20261103-1412
```

- **Status:** `proposed`, `approved`, `running`, `stopped: <prd>: <reason>`, `done` or `abandoned`.
- **Order:** from the members' links, upstream first. A cycle, or a member linked to no other
  member, is refused.
- **Location:** relative to the starting repository's root.
- **Branch:** `cs-<nnn>-<slug>` in every member, cut from that member's default branch.
- **Waits for:** for each upstream member, `<prd> <Needs of the link>`; `—` for none.
- **Target:** the highest Needs any downstream member has of this row, else `verified`. When two
  downstream members need different `live in` environments, the one later in the upstream's
  `operations.md` Environments table. Order of
  states: `proposed` < `approved` < `built` < `verified` < `live in <env>`.
- **State:** the row's place in that order. A stop is recorded on Status and in Log; the row keeps its State.

| `changeset` subcommand | Does |
|---|---|
| `new <PRD> --title <text> --member <location>…` | Numbers the record, reads every member's `links.md`, computes Order, Waits for and Target, writes `Status: proposed` |
| `set <record> <prd> <field>=<value>…` | Sets Branch, Version, IDs or State; refuses a State that goes backward or skips its Waits for |
| `approve <record> --reply <text> [--amendment]` | Quotes the reply on the Approval line (an amendment adds a dated line); moves every `proposed` row to `approved` |
| `stop <record> <prd> <reason>`, `log <record> <text>` | Records a stop (Status `stopped: <prd>: <reason>`, and Log) or a line in Log; `set` of any State moves Status back to `running` |
| `close <record>` | Refuses unless every row's State equals its Target; writes `Status: done` and a **Merge order** list, upstream first |
| `abandon <record> <reason>` | `Status: abandoned`; the branches are left for the user |

The caller commits each record write on the starting repository's change-set branch, with
`Refs: none (no behaviour change)` and the `Change-set:` trailer.

### Running a change set (`running-a-change-set.md`)

1. **Scope.** In the starting repository, `prd_links.py impact` lists the consumers that cite the
   items the change touches. The session confirms the members with the user, then runs
   `changeset new`. An unreachable consumer is never skipped: the user makes its clone available,
   or says in their own words that it stays out, and the Log quotes them.
2. **Edit.** In each member, in Order, on the record's branch, run `changing-prds` up to its
   approval: restate, edit, bump, lint, dry run. Then `sync --ref <branch>` in every downstream
   member, so lint checks the edits together, and `changeset set` the Version and IDs. Each upstream
   member's edit is committed on the branch, status `In review`, before a downstream member syncs;
   step 3's approval commit flips it to `Approved`. A session never begins a member's step 2 that it
   cannot finish: for a member that is not its own repository it logs the stop and stops, and that
   member's own session runs the whole step.
3. **One approval.** Show every member's PRD diff together and stop. One explicit reply approves
   the set: `changeset approve`, then each member's approval commit as `changing-prds` makes it, with
   the `Change-set:` trailer.
4. **Build in order.** For each row in Order, once its Waits for holds: `sync --ref <branch>` against
   each upstream member, then `/prd-build` in that member. When a downstream row waits for
   `live in <env>`, the upstream's `/prd-deploy --until <env>` runs before it, its human steps
   relayed as `deploying-from-prds` relays them. `changeset set` each State as it is reached.
5. **Stops.** A failed build, a human step without a reply, or an error stops the chain:
   `changeset stop`, and the rows after it wait. An error goes to that member's `/prd-error`. A fix
   that needs a PRD edit amends the change set: the amendment's diff is shown and approved alone
   (`approve --amendment`). A new session resumes from the record alone.
6. **Close.** When every row has reached its Target, `changeset close` writes the Merge order. The
   toolkit pushes and merges nothing; the user lands each member, upstream first. After an upstream
   lands, `sync` re-locks each downstream against the upstream's default branch, committed in the
   downstream. Production deploys stay per repository, through `/prd-deploy`, in Merge order.

**Sessions.** One record drives a change set. Record writes, `impact`, `sync`, `check` and deploys
run for any member from any session. A dry run and a build dispatch agents whose worktree and guard
bind to the session's own repository, so they run in a session started in that member's root, and
the chain resumes from the record in each.

## 7. Lint and trace

Lint stays offline and per repository: it reads `links.md`, the snapshot and the records, never
another repository. Agreement between the two sides is `prd_links.py check`'s, not lint's.

| Rule | Fails when |
|---|---|
| `links-format` | `links.md` has a wrong heading or table header; a slug is malformed or repeated in its table; a Location is neither a backticked path nor `<git URL>#<folder>`; a Version is not `X.Y.Z` or a Commit not 7–40 hex digits (both empty is allowed only before the first `sync`); a Needs value is outside the grammar |
| `upstream-refs` | a `<prd>/` reference names no Upstreams row, or its item is not in `contracts/upstream/<prd>/` |
| `snapshot-cited` | a snapshot item is cited nowhere, a snapshot folder has no Upstreams row, an Upstreams row is cited nowhere, or a snapshot file lacks its header line |
| `change-sets` | a record's heading, lines or table are malformed; a State, Status or Order is outside the grammar; an ID repeats; `Status: done` while a row's State is not its Target |

`test-refs` and `schema-refs` resolve the prefix through `upstream-refs`' resolver; they do not
report a prefixed reference twice. Prose rules (`placeholder`, `vague-word`, `glossary-synonym`) do
not read `contracts/upstream/` or `changes/`.

**Trace.** `commit-refs` checks a `Change-set:` trailer's form, `<prd>/CS-nnn`. When `<prd>` is this
repository's own PRD, the record must exist; elsewhere the trailer is a pointer and only its form is
checked. **The `commit-msg` hook** applies the same form check when a trailer is present.

## 8. Other tools

- **CI.** When `links.md` exists, the generated `prd-lint` job runs `prd_links.py check`. Exit 1
  fails the job; the job runs `check --ci`, which prints the unreachable side on exit 3 and passes. `prd_hooks.py` vendors
  `prd_links.py`, and the stale-CI check covers the new lines. In an upstream, the same job reads
  each reachable consumer's snapshot, so an upstream merge that breaks a cited item fails there too.
- **Deploy pre-flight.** `prd_deploy.py run` refuses to start (exit 2, naming the drifted items)
  when `prd_links.py check` exits 1. Exit 3 is reported and does not refuse.
- **`/prd-status`.** Upstreams (lock, Needs, the verdict counts of `check`, for a path location only; a git URL location shows `check: not run`), Consumers, and
  each record under `changes/` that is not `done` or `abandoned`, with its rows' States.
- **`prd_context.py`.** A task whose `Touches:` or test cases cite a `<prd>/` reference gets the
  cited snapshot items in its pack.
- **The tester guard.** No change: the snapshot is inside the PRD folder.
- **`/prd-publish`.** Renders `links.md` with the rest of the PRD's text.

## 9. Skills and commands

**`coordinating-prds`** and **`/prd-change-set [<CS-nnn> | <text>]`.** It triggers when a change
touches a contract item another PRD cites, when asked to change something across repositories,
when resuming a CS-nnn, and on `/prd-change-set`. Its first instruction is to Read
`running-a-change-set.md` whole. Its rules:
1. One record per change set, written only by `prd_links.py changeset`.
2. One approval for the whole set of PRD diffs, quoted; an amendment gets its own.
3. A downstream build never starts before its Waits for holds.
4. A snapshot changes only through `prd_links.py sync`, never by editing it.
5. Nothing is pushed, merged or opened as a PR.
6. A failure stops the chain and goes to that member's `/prd-error`.

**`changing-prds`.** After the restate, when `links.md` has Consumers, run `prd_links.py impact`
on the edited PRD. Exit 1 or 3 stops the change and hands it to `/prd-change-set`; that is the only
route for an edit to a cited item.

**`running-a-build.md`.** On a change-set branch, the build syncs each upstream member's snapshot
before the dispatch and adds the `Change-set:` trailer to its commits (the dispatch passes it to `prd-builder`, which carries it); its close reports the state
reached, and the caller writes it with `changeset set`.

**`deploying-from-prds`.** No procedure change; a change set calls it with `--until <env>`.

**`authoring-prds`, `adopting-prds`.** When the project consumes or provides another PRD's
contract items, they propose `prd_links.py add`. Adoption discovers such links from the code (a
table read from another repository's output, an API called), as it discovers registry rows.

## 10. F-a and O-a

**F-a.** The clarify categories gain **packaging**: the build backend, the package layout, the
entry points and the install command. The interview asks it whenever the project ships code, and
`quality-checklist.md` gains its line.

**O-a.** A headless `--plugin-dir` session on the current Claude Code is probed for the bare
`/prd-*` commands. If they still do not register, the cause is the platform: the README says
headless runs invoke `prd-toolkit:<command>`, and the evals and the acceptance procedure use that
form on purpose. If they register, the observation is closed. Either way the acceptance note
records the finding.

## 11. Changes to existing text

- `prd-format.md`: `links.md`, the prefix, the snapshot and its header, the record, the trailer.
- `clarify-categories.md`, `quality-checklist.md`: packaging.
- `changing-prds`, `running-a-build.md`, `authoring-prds`, `adopting-prds`: section 9.
- `templates/claude-block.md`: the coordination role, when `links.md` exists.
- The README: Links, Change sets, O-a, the upgrade note.
- The base spec §3 gains a revision note pointing here.

## 12. Testing the toolkit

1. **Scripts (pytest).** Every finding is proven able to fail before it is trusted. A
   `make_linked_repos()` helper builds an upstream and a downstream git repository in a temporary
   directory, each with a PRD, `links.md` and a snapshot; nothing with a `.git` is committed.
   - `add`: both sides written; the printed row when the other side is a URL; each refusal.
   - `sync`: only cited items copied (an uncited table never reaches the snapshot), the `$ref`
     closure for `op`, the header line, the lock; the refusal for a missing item writes nothing.
   - `check`: `same`, `changed`, `removed`, `newer than lock`, an orphaned lock after a squash
     merge, a missing row on either side, exit 3 for an unreachable side.
   - `impact`: the right consumers and items; exit 3.
   - `changeset`: numbering, Order, a refused cycle, each refused State, `close` refused early, the
     Merge order.
   - Each new lint rule with a failing and a passing fixture; the prefix in `test-refs` and
     `schema-refs`; the trailer in trace and the hook; status, context pack, deploy pre-flight; the
     vendored copy and the stale-CI check.
2. **Baselines before the skill** (`writing-skills`, RED first, recorded verbatim in
   `evals/baselines/`):

   | ID | Pressure |
   |---|---|
   | C1 | "The upstream is basically done; start the downstream build" |
   | C2 | "Just edit the snapshot to match" |
   | C3 | "Approve each repository as we go" |
   | C4 | "That consumer isn't cloned here; skip it" |
   | C5 | "Push the branches so CI runs" |

3. **Evals:** `coordinating-prds` triggers on a cross-repository change and on resuming a CS-nnn; a
   single-repository change stays with `/prd-change`; `changing-prds` hands off when `impact` exits
   1; no hand edit of a snapshot; no downstream build before its Waits for; no push. F-a: the
   interview asks about packaging.

## 13. Proof: hello-world, slice 4

Headless, as in 0.5 and 0.6. The scaffold builds two sibling repositories:
- `greet` at slice 3's end, plus a patch that adds a custom contract type `cli`
  (`contracts/cli.yaml`, one top-level key per command: arguments, output, exit codes) with its
  validator, deployed to staging;
- `greet-client`, an approved and verified PRD for `welcome <name>`, which runs the staging install
  of `greet` and prints a banner around its greeting, with a deploy-gate system test. It has no
  links yet.

| # | Run | Pass line |
|---|---|---|
| Q1 | `/prd-change` in `greet-client`: cite `cli:greet/greet` | `add` writes both sides; `sync` copies only the `greet` key; both repositories' lint and `check` exit 0 |
| Q2 | `/prd-change-set` from `greet`: `greet --json` prints `{"greeting": …, "name": …}`, and the client reads it | `impact` names the client; CS-001 written; both PRDs edited and approved by one reply; `greet` built, deployed to staging; the client synced and built; `close` writes the Merge order; every row at its Target, with a resume in `greet-client`'s own session for the steps that dispatch agents there |
| Q3 | Q2's session ended once `greet` is `verified` | A new session resumes from the record alone and continues with `greet`'s staging deploy |
| Q4 | An edit to `greet`'s `cli.yaml` outside a change set | `check` exits 1 in both repositories; with `greet` moved away, the client's `check` exits 3 and its CI job passes |
| Q5 | `greet`'s change-set branch squash-merged into `main` | `check` flags the orphaned lock; `sync` clears it |
| Q6 | `/prd-change` in `greet` touching `cli:greet` with the client clone moved away | `impact` exits 3; the change stops and hands off without skipping the client |

The verdict goes to `docs/superpowers/plans/2026-11-02-prd-toolkit-0.7-acceptance.md`, with the O-a
finding.

## 14. Upgrade from 0.6

- Re-run `prd_hooks.py install` (vendors `prd_links.py`) and `prd_hooks.py ci` (the `prd-lint` job
  gains the link check when `links.md` exists).
- A PRD without `links.md` needs no edit.

## 15. Known limits

- A git URL location is read with the user's own credentials; CI without them gets exit 3, so CI
  catches a break only where the other side is reachable.
- An upstream sees a consumer's citations only through that consumer's committed snapshot.
- Only the kinds of section 4 cross repositories; a non-YAML custom type cannot be cited across.
- Every member must be cloned on the machine running the change set, and a dry run or a build of
  a member runs in a session started in that member's root, so a change set takes one resume per
  member.
- An item of `contracts/asyncapi.yaml` cannot be cited across repositories (`asyncapi items cannot be
  cited across repositories`).
- `/prd-status` runs the link check for path locations only.
- An approval is trusted to be the user's, as 0.5's `confirm`.

## 16. Out of scope for 0.7

- Nightly drift and smoke runs, `prd-error` issues, schema drift.
- More than one PRD per repository.
- The toolkit pushing, merging or opening a pull request.
- Adding skills and plugins, any output language, converting a project, best-practice sources (0.8).
