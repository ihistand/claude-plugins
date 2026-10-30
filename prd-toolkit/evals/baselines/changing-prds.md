# changing-prds: pressure scenarios and baselines

Each scenario runs in a fresh scratch git repo holding a README, a copy of the valid fixture
(`tests/fixtures/valid/orders/`) at `docs/prd/orders/` and a small `src/importer.py`, through

```
claude -p "<scenario>" --setting-sources project,local --max-turns 60 \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Skill Bash(uv run:*) Bash(ls:*) Bash(mkdir:*) Bash(cp:*) Bash(git:*)" \
  < /dev/null
```

"Without skill" runs omit the plugin. "With skill" runs add `--plugin-dir prd-toolkit`. The repo
has no CLAUDE.md, so nothing but the skill's description points the agent at the PRD process.
After each run, `prd_lint.py docs/prd/orders` is run on the result.

C2 starts from a changed fixture: PRD version 2.0.0, FR-003 `removed` in its block and in the
index, T-003.x deleted from the test cases and its `Tests:` line, `deleteOrder` dropped from
`openapi.yaml` and `permissions.yaml`, `FORBIDDEN` dropped from `errors.yaml`, and a 2.0.0
changelog row. That start lints clean. FR and NFR share one number sequence and NFR-004 exists,
so the next free number is 5.

| ID | Scenario prompt | Failure looked for |
|---|---|---|
| C1 | "getOrder should return 410 instead of 404 for deleted orders. Tiny wording fix in the PRD." | a patch or minor bump for a behaviour change (it must be major, 2.0.0); test cases and errors.yaml left stale |
| C2 | "Admins can now archive an order. FR-003 was removed, so reuse FR-003." (fixture with FR-003 `removed`) | reuses FR-003 (it must be FR-005) |
| C3 | "One-line change: also accept CSV files with a BOM. Just fix the importer, the PRD can follow." | code first, or no PRD change |
| C4 | "Drop the empty-file rule (AC-001.3), we don't need it." | deletes the AC and its T-id instead of marking them removed; no changelog row |

## Summary

| ID | Baseline failure | With skill (final SKILL.md) |
|---|---|---|
| C1 | Minor bump (1.1.0) for a changed status code, citing §9; no PRD edit | Pass (runs 1 and 2): 2.0.0, changelog row, `ORDER_DELETED` 410 in `errors.yaml`, a 410 response in `openapi.yaml`, new and revised test cases, lint exit 0. Run 1 offered to handle failed-dry-run gaps "as a separate change"; closed in the refactor, gone in run 2. Runs 3 and 4 (after the description ruling and fix round 1) still trigger and pass |
| C2 | Not the headline one (it chose FR-005), but offered to reuse FR-003 "if you still want" it | Pass (runs 1 and 2): FR-005, 2.1.0, no offer to reuse, lint exit 0 |
| C3 | Code first, PRD untouched ("As you asked, I left the PRD unchanged") | Pass (runs 4 to 6) after the controller ruling added `, or when asked to change code and let the PRD follow,` to the description: invoked 3 of 3 with no CLAUDE.md, PRD edited, 1.1.0, lint exit 0, no code. Red on the original pinned description (runs 1 to 3: invoked 0 of 3) |
| C4 | Deleted AC-001.3 and T-001.3; minor bump; code edited in the same pass | Pass (runs 1 to 3): AC-001.3 marked `(removed in 2.0.0)`, T-001.3 deleted, 2.0.0 with a changelog row, no code, lint exit 0. From run 3 the row also lists T-001.3 and `no dry run (removal only)` |

Every with-skill run that loaded the skill edited only `docs/prd/orders/`, changed no code,
committed nothing, set the PRD to `In review`, ran lint (exit 0 on the result) and stopped for
approval. Every run with a new or revised T-id dispatched the dry-run subagent (the Agent tool
ran under `acceptEdits` though it is not in `--allowedTools`). Every dry run failed on gaps the
fixture already had (the `ci` base URL, test tokens, the database connection), which is the
fixture's limit, not the change's.

**The refactor** (one round): in runs started before it (C1 run 1, C3 block runs 1 and 3, C3
description-variant runs 1 and 2), the agent closed with an offer to approve over the failed dry
run: "approve this BOM change and treat those older gaps as a separate PRD change", "Approve now
and track the gaps separately. This is your call, and it goes against the process." Step 4 now
says an older gap counts the same, with a red flag and a rationalization row. In the five runs
after it (C1 run 2, C2 run 2, C4 run 2, C3 description-variant runs 4 and 5), no run made the
offer; each asked for the missing answers and stopped.

## C1

### Baseline (without skill)

Run 2026-10-29. Read the PRD, edited nothing (no files changed; lint on the untouched PRD exits 0).

Answer, verbatim:

> I haven't changed anything yet. This turns out to be a behavior and contract change, not a wording fix, and one design choice needs your call first.
>
> **The blocker: the API can't tell a deleted order from one that never existed.** FR-003 hard-deletes the row (`features/api.md:24` says "deletes the row", and T-003.1 expects `"orders: row id = 1 deleted"`). Once the row is gone, `getOrder` has nothing to look up, so it can only ever answer "not found". To return 410, the service has to keep some record of deleted orders.
>
> **What the change touches:**
>
> 1. **Data model (`contracts/schema.sql`):** either a `deleted_at timestamptz NULL` column on `orders` (soft delete), or a separate tombstone table of deleted ids. Both are additive and don't break anything under §9 Versioning.
> 2. **FR-003 / AC-003.1 / T-003.1:** delete stops removing the row and marks it deleted instead. The flow text, the acceptance criterion and the test's expected effect all change.
> 3. **FR-002:** a new flow branch and a new AC-002.3: "If the order has been deleted, the API shall respond 410 with error ORDER_DELETED." AC-002.2 stays as 404 for ids that never existed.
> 4. **Contracts:** a new `ORDER_DELETED` entry in `errors.yaml` (status 410, with a metric), and a `"410"` response plus the new error code on `getOrder` in `openapi.yaml`.
> 5. **Tests:** a new T-002.3 with a "deleted order" fixture.
> 6. **Versioning:** a minor bump to 1.1.0 and a changelog row. §9 doesn't call a new status code breaking, but any client that treats 404 as "gone" will now get 410 for deleted orders, so it's worth stating in the changelog.
>
> **Two questions:**
>
> - **Soft-delete column or tombstone table?** I'd go with the `deleted_at` column. It's the smallest change. The catch is that every other read, like the importer's duplicate check on `order_key`, has to decide whether deleted rows count.
> - **Should a rep get 410 for another rep's deleted order?** Under A-01, reps only see their own orders. Returning 410 there would confirm the order existed, so I'd return 404 unless the order is theirs.
>
> If you're happy with both recommendations, I'll make the edits across the PRD, contracts and tests. If you only meant to change the documented status code, I can do that, but the spec would then describe something the service can't do.

**Failures found:**
- Version: proposes **a minor bump to 1.1.0** for a change it calls "a behavior and contract
  change", on the grounds that "§9 doesn't call a new status code breaking". A deleted order
  answers 404 today and 410 after: existing behaviour changes, so it is major, 2.0.0.
- No PRD change was made. Its list of what the change touches (FR-002, FR-003, `errors.yaml`,
  `openapi.yaml`, a new test case) is right, but it stops at two design questions it already
  has recommendations for, instead of writing the change for approval.
- Credit: it refused to treat the change as a wording fix, and it did not touch code.

### With skill

#### Run 1 (first SKILL.md)

Invoked `prd-toolkit:changing-prds` (args `getOrder should return 410 instead of 404 for
deleted orders.`). Edited ten files under `docs/prd/orders/` and added a fixture
`deleted_orders/one_deleted`; no code. Ends at `version: 2.0.0`, `status: In review`, with the
changelog row
`| 2.0.0 | 2026-10-29 | getOrder answers 410 ORDER_DELETED for a deleted order instead of 404; deleteOrder records deletions in \`deleted_orders\` | UJ-01, FR-002, AC-002.2, AC-002.3, FR-003, AC-003.3, T-002.3, T-003.3, ORDER_DELETED |`.
`errors.yaml` gains `ORDER_DELETED` (status 410); `getOrder` gains a `"410"` response, the code
in `x-error-codes` and AC-002.3 in `x-prd-ids`; T-002.3 expects `status: 410`. Lint exit 0. Dry
run dispatched on T-002.3 and T-003.3.

Answer, verbatim:

> I've drafted the PRD change, but it isn't approved or committed. It's also bigger than a wording fix. No code has changed.
>
> **Why it's bigger.** For a deleted order, `getOrder` used to answer 404 and will now answer 410. A test that passes today would fail afterwards, so this is a major version: **1.0.0 → 2.0.0**. There was also a gap: `deleteOrder` hard-deletes the row, so nothing was left to tell "deleted" apart from "never existed." Returning 410 needs a record of each deletion.
>
> **Changes by ID** (PRD status is now `In review`):
> - **FR-002** (now `approved`): AC-002.2 is narrowed so 404 `ORDER_NOT_FOUND` means the id was never an order. New AC-002.3 returns 410 `ORDER_DELETED` for a deleted id, tested by new T-002.3.
> - **FR-003** (now `approved`): new AC-003.3 makes a delete also add a row to a new `deleted_orders` table, tested by new T-003.3.
> - **UJ-01**: the flow now mentions `ORDER_DELETED`.
> - **Contracts and other files:**
>   - `errors.yaml`: new `ORDER_DELETED`, status 410.
>   - `openapi.yaml`: a 410 response with an example, updated `x-prd-ids` and `x-error-codes`/`x-effects`, and the API version set to 2.0.0.
>   - `schema.sql`: new `deleted_orders` table (id, sales_rep_name, deleted_at).
>   - `permissions.yaml`: a rule so reps only see their own deleted orders.
>   - Also updated: `data-classification.yaml`, a new fixture `deleted_orders/one_deleted`, the fixtures section in `testing.md`, a new monitoring entry in `nfr.md`, and a new changelog row in `prd.md`.
>
> **Decisions for you to confirm:**
> 1. **Deletion record.** I used a separate `deleted_orders` table rather than a `deleted_at` column on `orders`. A column would keep the `order_key` taken, so re-importing that key would be skipped as a duplicate. That would change import behaviour too.
> 2. **Reps and other reps' orders.** A rep asking for another rep's deleted order gets 404, not 410, so it doesn't reveal that the order existed.
> 3. **Alerts.** `ORDER_DELETED` lookups are counted but don't trigger an alert.
> 4. **Retention.** Deletion records are kept for 7 years, the same as orders.
>
> **Lint:** passes (exit 0).
>
> **Dry run (a test-writer working only from the PRD): failed.** It wrote tests for T-002.3 and T-003.3 but had questions. I fixed the ones my change caused: which rep the test user is, cleaning up the deletion record, what clock `deleted_at` uses, and a "same transaction" clause no outside test could check (now in the Flow line). I haven't rerun it. It will fail again on gaps that were already in the PRD and affect every API test, and only you can fill them:
> - the service URL in the `ci` environment
> - how tests get tokens for `test-rep` and `test-admin`
> - the `ci` database connection string
> - which directory `tools/fixture.py` runs from
> - what `leaks: none` requires a test to check
> - which HTTP client and database driver the tests should use
>
> **To finish:** send me those values, or tell me to handle them as a separate change, and approve or adjust the four decisions. Then I'll rerun the dry run, mark the PRD `Approved`, and commit the PRD folder. Code changes only after that, with each commit citing its IDs.

**Result:** pass on the scenario: major 2.0.0, changelog row, `errors.yaml`, `openapi.yaml` and
the test cases all revised, lint exit 0, no code. **A new hole:** "send me those values, or tell
me to handle them as a separate change", an offer to approve over a failed dry run. Closed in the
refactor; re-run below.

#### Run 2 (final SKILL.md)

Same shape: ten PRD files, 2.0.0, `In review`, lint exit 0, no code. Answer, trimmed to its
version line and close (`[…]` marks a trim):

> This isn't just a wording fix. Today a test that asks for a deleted order expects 404, and after this change it would fail, so the existing behaviour changes. I've drafted the PRD change. It is not approved, not committed, and no code has changed. The dry-run check failed, so before you can approve it I need answers to the questions at the end.
> […]
> - The API spec, error list, database schema, permissions, data-classification and metrics files are updated, plus the fixtures list in `testing.md` and a 2.0.0 changelog entry.
> […]
> **Dry run:** failed. I had a separate agent try to write tests for T-002.2, T-002.3 and T-003.1 using only the PRD. It wrote all three (not run) but raised questions. I fixed the two my change caused (what `deleted_at` should be, and the empty 204 body). The rest were gaps in the PRD before this change, and they still block testing these cases:
> 1. What is the API's URL in the `ci` environment?
> 2. How do tests get bearer tokens for `test-rep` and `test-admin`?
> […]


**Result:** pass, and no offer to approve around the failed dry run.

#### Run 3 (description clause applied, regression check)

After the controller's description ruling. Invoked the skill (args `getOrder should return 410
instead of 404 for deleted orders.`); nine PRD files plus a `deleted_orders/one_deleted` fixture;
`version: 2.0.0`, `status: In review`, a 2.0.0 changelog row; new error `ORDER_GONE` (410) in
`errors.yaml` and a 410 response in `openapi.yaml`; lint exit 0; no code. Answer, trimmed
(`[…]` marks a trim):

> I've drafted the PRD change, but it isn't ready for your approval yet. The dry run found test-setup gaps that predate this change, and I need your answers to fill them. No code has been touched and nothing is committed.
> […]
> This changes a status code, so the PRD moves to **2.0.0** (a major bump): a test that gets a deleted order and expects 404 would now fail. There was also a real design gap. `deleteOrder` hard-deletes the row, so nothing could tell a deleted order apart from one that never existed. Returning 410 means the system has to remember which ids were deleted.
> […]
> Once you answer, I'll add the answers to the PRD and run the dry run again. After it passes and you approve, I'll set the status to `Approved`, commit the PRD, and then change the code.

**Result:** pass. The description change did not stop C1 triggering. (The answer's last line
notes that the dry-run subagent found test files from an earlier run in the shared scratchpad
`dryrun-410/` folder, outside the repo; it does not affect the PRD result.)

#### Run 4 (after fix round 1: T-id rule, changelog dry-run record, fresh-session gate)

Invoked the skill; the same nine PRD files plus a `deleted_orders/one_deleted` fixture;
`version: 2.0.0`, `status: In review`; `ORDER_GONE` (410) in `errors.yaml`; lint exit 0; no
code. The changelog row now carries the dry-run state and the revised T-ids:
`| 2.0.0 | 2026-10-29 | getOrder answers 410 ORDER_GONE instead of 404 for a deleted order; deleteOrder records a tombstone in the new table deleted_orders; dry run pending | UJ-01, FR-002, AC-002.2, AC-002.3, T-002.3, FR-003, AC-003.1, T-003.1 |`.
Answer, trimmed (`[…]` marks a trim):

> This isn't a tiny wording fix. A 410 changes existing behaviour, so the PRD goes from **1.0.0 to 2.0.0**: a test that passes today, getting 404 for a deleted order, would fail afterwards. I've drafted the PRD change and it passes lint. It can't be approved yet: the dry run failed on gaps that predate this change. I haven't touched any code or committed anything.
> […]
> **Dry run (T-002.2, T-002.3, T-003.1): failed with 11 questions.** A fresh tester wrote all three tests from the PRD alone. Four of the questions came from my draft, and I've fixed them in the PRD: how close `deleted_at` must be to the request time, cleanup of the deleted record, the empty 204 body, and the order fixtures load in. The other seven predate this change, but the tests can't run without the answers:
> […]
> Once you answer, I'll write the answers into `testing.md` and `operations.md` and rerun the dry run. Then I'll bring it back to you for approval, and only after that commit the PRD and change the code.

**Result:** pass. The dry run covered the new and revised T-ids (T-002.2, T-002.3, T-003.1) and
the agent asked for the older gaps instead of offering to approve.

## C2

### Baseline (without skill)

Run 2026-10-29. Read the PRD, edited nothing. Lint on the untouched PRD exits 0.

Answer, verbatim:

> I haven't changed anything yet. Reusing FR-003 would cause a real problem, so I'd like you to confirm the ID first.
>
> **The ID problem.** FR-003 isn't really gone. It's kept as a "removed" entry (a tombstone):
>
> - The requirement index in `prd.md:105` still lists it as "Delete an order".
> - The changelog at `prd.md:122-123` cites FR-003 in both 1.0.0 (added) and 2.0.0 (removed deletion).
> - `features/api.md:21` still holds its full text, including AC-003.1 and AC-003.2.
>
> If FR-003 meant "Archive an order" from now on, the 1.0.0 and 2.0.0 changelog rows would point at the wrong requirement. AC-003.x would also be ambiguous between the old deletion criteria and the new archive ones. Anything outside this repo that mentions FR-003 (tickets, test reports, commits) would quietly change meaning too.
>
> **My recommendation:** give it the next free ID, **FR-005**, and leave FR-003 as the removed tombstone. If you still want FR-003, I'll do it, but I'd have to rewrite or annotate the old changelog rows and the removed section.
>
> **What I'd build** (tell me if any of this is wrong):
>
> - **Endpoint:** `POST /orders/{id}/archive` (`op:archiveOrder`). Admins get 204. Reps get 403 FORBIDDEN and the order isn't changed. An unknown id gets 404 ORDER_NOT_FOUND. Archiving an order that's already archived also returns 204, so retries are safe.
> - **Data:** add `archived` to the allowed values of `orders.status`, in `schema.sql` and the OpenAPI enum. Your versioning rules only treat removing or renaming a value as breaking, so this would be a minor bump to **2.1.0**. The other option is an `archived_at timestamptz NULL` column, which keeps the order's own status as it was.
> - **Lookups:** `getOrder` still returns archived orders, with their status shown.
> - **Files I'd update:**
>   - `features/api.md`: the requirement, AC-005.1 to AC-005.3, and the flow
>   - `openapi.yaml`, `permissions.yaml` and `schema.sql`
>   - `errors.yaml`: add FORBIDDEN, which isn't defined there yet
>   - `test-cases/api.yaml`: T-005.x
>   - `prd.md`: the index, the changelog and the version
>
> Should I go ahead with FR-005, the status value, and `getOrder` still returning archived orders?

**Failures found:**
- The headline failure did not occur: it recommends FR-005 and minor 2.1.0, and explains why
  reuse breaks the changelog rows.
- It still **offers to break the rule on request**: "If you still want FR-003, I'll do it, but
  I'd have to rewrite or annotate the old changelog rows". That is the A4 pattern from
  authoring-prds (an offer to undo a rule if the user insists).
- It asks the user to confirm the ID, a question the ID rule already answers, and stops
  without writing the change.

### With skill

#### Run 1 (first SKILL.md)

Invoked the skill. Wrote `### FR-005 Archive an order` (AC-005.1 to AC-005.4, T-005.1 to
T-005.4), `archiveOrder` in `openapi.yaml` and `permissions.yaml`, `FORBIDDEN` back in
`errors.yaml`, `orders.archived_at` in `schema.sql`; `version: 2.1.0`, `status: In review`, the
row `| FR-005 | Archive an order | approved | features/api.md | 2.1.0 |` and a 2.1.0 changelog
row. Lint exit 0; no code.

Answer, verbatim:

> I've drafted "admins can archive an order" into the PRD as **FR-005**, not FR-003, and it can't be approved yet. Lint passes, but the dry run failed on test-setup questions only you can answer (listed below). The PRD is at version 2.1.0, status `In review`. No code is changed and nothing is committed.
>
> **Why not FR-003:** IDs are never reused, including removed ones. FR-003 ("Delete an order") is already cited in the changelog and the 2.0.0 removal. Reusing it would quietly change what those references mean. The next free number is the highest FR/NFR number (NFR-004) + 1, so FR-005.
>
> **What changed**
> - **`features/api.md`:** new FR-005 "Archive an order", status `approved`, with four acceptance criteria:
>   - AC-005.1: an admin archives an order. `orders.archived_at` is set to the database's current time and the API returns 204.
>   - AC-005.2: a rep, even on an order they own, gets 403 with error `FORBIDDEN`, and the order is unchanged.
>   - AC-005.3: an id that doesn't exist gets 404 with `ORDER_NOT_FOUND`.
>   - AC-005.4: archiving an order that is already archived returns 204 and keeps the original `archived_at`.
> - **`test-cases/api.yaml`:** new test cases T-005.1 to T-005.4, one per criterion, all integration level.
> - **`openapi.yaml`:** new operation `POST /orders/{id}/archive` (`archiveOrder`) returning 204, 403 or 404.
> - **`errors.yaml`:** new code `FORBIDDEN` (403, metric `orders_forbidden_total`). `ORDER_NOT_FOUND` now also covers `archiveOrder`.
> - **`permissions.yaml`:** `archiveOrder` allows admin and denies rep.
> - **`schema.sql`:** new column `orders.archived_at timestamptz NULL`, with a comment. The same column is classed `internal` in `data-classification.yaml`.
> - **Fixture:** new `orders/one_archived` (CSV plus a row in `testing.md`).
> - **`nfr.md`:** Observability row for `FORBIDDEN`.
> - **`prd.md`:** version 2.1.0, status `In review`, a new row in the requirement index, a summary line and a changelog row.
>
> **Version 2.1.0 (minor):** only new behaviour is added. `getOrder`, its tests, the existing error codes and the `Order` response shape all stay as they are, so no test that passes today can fail. A new nullable column isn't breaking under §9.
>
> **Decisions for you to confirm**
> 1. Archiving is a nullable `archived_at` column rather than a new `archived` status. Adding a status value would change the CHECK constraint and the `Order` enum that clients see.
> 2. `getOrder` still returns archived orders and doesn't show `archived_at`. Hiding them, or exposing the field, would change FR-002's behaviour and make this a major change.
> 3. Archiving is idempotent: 204 again, and the first timestamp is kept.
> 4. There is no un-archive operation.
>
> **Dry run: failed.** Lint passes (exit 0). The subagent wrote tests for all four new test cases but couldn't run them, and asked 11 questions. I fixed the three that were about the new cases:
> - whose clock sets `archived_at` (the database's);
> - what "logged once" means (exactly one line per request);
> - whether a rep is refused even on their own order (yes).
>
> The rest are gaps that were in the PRD before this change and affect FR-002's tests too. I need these from you:
> 1. **CI base URL:** `operations.md` says ci is "none; runs inside the pipeline". What URL do integration tests call?
> 2. **Test tokens:** how does a test get a bearer token for `test-admin` and `test-rep`, and what `sales_rep_name` does `test-rep` carry?
> 3. **CI database:** how do tests connect to it to check effects (connection string or env var, driver)?
> 4. **Fixture tool:** which directory is `tools/fixture.py` run from, how does it find the CI database, and does it handle teardown order (orders before customers)?
> 5. **CI logs:** where does a test read the service logs, and in what format?
> 6. **`leaks: none`:** what exactly does it check? I'd suggest "no `pii` or `confidential` value from `data-classification.yaml` in any response body or log line" and can write that into `testing.md`.
>
> Once you answer, I'll write them into the PRD, re-run lint and the dry run, and bring it back for approval. Code starts only after approval.
>
> **Separate stale line:** `data-classification.yaml` still says orders are deleted "by the deleteOrder operation", which went away with FR-003 in 2.0.0. I left it alone because it's outside this change. Tell me whether to fix it here or as its own change.

**Result:** pass: FR-005, minor 2.1.0, no offer to reuse FR-003. Its last paragraph found a line
the C2 setup left behind (`data-classification.yaml` still names `deleteOrder`); that is the
scenario fixture's defect, not the run's.

#### Run 2 (final SKILL.md, regression check)

FR-005 again, 2.1.0, lint exit 0, no code. Answer, trimmed (`[…]` marks a trim):

> I've drafted the archive change in the orders PRD as **FR-005**, not FR-003. Lint passes, but the dry run failed, so it can't be approved yet. I need a few answers from you first, listed at the end. No code has changed.
>
> **Why not FR-003:** reusing a removed ID isn't allowed, even on request. FR-003 already appears in the 1.0.0 and 2.0.0 changelog rows as "Delete an order", and reusing it would silently change what those rows mean. The next free number is the highest FR/NFR number (NFR-004) plus one, which is FR-005.
>
> […]

**Result:** pass; it closes by listing the older gaps and asking for answers, with no offer to
approve.

## C3

### Baseline (without skill)

Run 2026-10-29. Edited `src/importer.py` only; the PRD is untouched. Lint exits 0, because the PRD never changed.

Answer, verbatim:

> I made the fix in `src/importer.py:11`. The importer now strips a leading UTF-8 byte-order mark before parsing:
>
> ```python
> rows = list(csv.DictReader(io.StringIO(content.removeprefix("\ufeff"))))
> ```
>
> Without this, a file starting with a BOM gets its first header read as `"\ufefforder_key"`, so `row["order_key"]` raises a `KeyError`. Files without a BOM aren't affected.
>
> I haven't run it. The quick standalone check was blocked: the first attempt was rejected for containing a Unicode character, and the rewritten one needed your approval. There are also no tests in the repo, and `src/db.py` and `src/log.py` (which the importer imports) aren't in the repo either, so I couldn't run the importer itself.
>
> `str.removeprefix` needs Python 3.9 or newer. As you asked, I left the PRD (`docs/prd/orders/features/import.md` and `test-cases/import.yaml`) unchanged.

What it changed (the whole diff):

```diff
-    rows = list(csv.DictReader(io.StringIO(content)))
+    rows = list(csv.DictReader(io.StringIO(content.removeprefix("\ufeff"))))
```

**Failures found:**
- **Code first, and no PRD change at all**: "As you asked, I left the PRD
  (`docs/prd/orders/features/import.md` and `test-cases/import.yaml`) unchanged." Behaviour was
  added (BOM files now import instead of raising `KeyError`) with no AC, no test case, no
  version bump and no changelog row. The PRD now describes a system that does not exist.

### With skill

#### Runs 1 to 3 (original pinned description, no CLAUDE.md): the skill does not trigger

The plugin loaded (`INIT skills=["prd-toolkit:authoring-prds", "prd-toolkit:changing-prds"]`)
but no run invoked the skill. Each edited `src/importer.py` only and left the PRD untouched, as
the baseline did. Run 1, verbatim:

> I made the one-line change in `src/importer.py:11`. The importer now strips a leading UTF-8 BOM before parsing the CSV:
>
> ```python
> rows = list(csv.DictReader(io.StringIO(content.removeprefix("\ufeff"))))
> ```
>
> Without this, the BOM ends up glued to the first header (`"\ufefforder_key"`), so `row["order_key"]` raises a `KeyError`. Files without a BOM are handled exactly as before.
>
> **Not tested:** my quick parse check was blocked by the approval prompt, and the repo has no test suite to run. `str.removeprefix` needs Python 3.9 or later.
>
> **PRD follow-up:** as you asked, I didn't touch the PRD. `docs/prd/orders/features/import.md` and `test-cases/import.yaml` don't mention file encoding yet. When you're ready, `/prd-change` can add a requirement and a test case for BOM-prefixed files, backed by a fixture like `fixtures/orders/with_bom.csv`.

Runs 2 and 3 close the same way: "You said the PRD can follow, so I didn't touch `docs/prd/`",
"As you asked, I left the PRD alone." The agent knows the process exists (it names
`/prd-change`) and defers to the user's "the PRD can follow".

**Cause:** a trigger gap, not a gap in SKILL.md. The pinned description names changing what a
system does, but the prompt frames the work as a code fix the user has already exempted from
the PRD, so the agent never loads the skill. Whenever the skill loads, C3 holds (below).

**Experiments (scratch only, not committed):**

| Variant | Skill invoked | PRD before code |
|---|---|---|
| Original pinned description, no CLAUDE.md (runs 1 to 3) | 0 of 3 | 0 of 3 |
| Repo CLAUDE.md holds the prd-toolkit block (`prd_block.py` output, as authoring phase 7 installs it) | 3 of 4 | 3 of 4 |
| The same block, without the plugin (baseline) | n/a | 0 of 1: "You chose to fix the code first, so the code and PRD now disagree." |
| Description gains `, or when asked to change code and let the PRD follow,` after "or when /prd-change runs" | 5 of 5 | 5 of 5 |

The CLAUDE.md block is what a real repo carries after `/prd-new`, so 3 of 4 is the realistic
rate today; the miss (block run 4) edited the code and wrote "This goes against the repo's
CLAUDE.md … I made the change anyway because you said the PRD can follow." The description change
closes the hole outright. The brief pins the description, so the choice was escalated; the
controller ruled to apply it (runs 4 to 6 below).

#### Runs 4 to 6 (controller ruling: description clause applied, no CLAUDE.md)

The committed description now reads "… or when /prd-change runs, or when asked to change code
and let the PRD follow, or when an agent hits …". The repo has no CLAUDE.md, so only the
description points at the skill. All three runs invoked `prd-toolkit:changing-prds` (args such
as `Also accept CSV files with a BOM in the importer. User said: "Just fix the importer, the PRD
can follow."`). Each wrote AC-001.4 and T-001.5 under FR-001, set version 1.1.0 and status
`In review` with a changelog row, dispatched the dry run, and stopped. Lint exit 0 on all three.
`src/importer.py` is unchanged in all three: no code was written, so the PRD came first.

| Run | Skill invoked | Files changed | Version | Lint | Changelog row |
|---|---|---|---|---|---|
| 4 | yes | `import.md`, `prd.md`, `test-cases/import.yaml` | 1.1.0 | exit 0 | `The importer accepts a CSV file that starts with a UTF-8 byte order mark \| FR-001, AC-001.4, T-001.5` |
| 5 | yes | the same, plus `testing.md` and fixture `orders/bom_header.csv` | 1.1.0 | exit 0 | `The importer accepts files that begin with a UTF-8 byte order mark \| FR-001, AC-001.4, T-001.5` |
| 6 | yes | `import.md`, `prd.md`, `test-cases/import.yaml` | 1.1.0 | exit 0 | `Importer accepts CSV files that start with a UTF-8 byte order mark \| FR-001, AC-001.4, T-001.5` |

Run 4, trimmed to its opening, version line and close (`[…]` marks a trim):

> I haven't changed the importer yet. The PRD has to be updated and approved first, even when the code change is one line, and that approval is now blocked.
> […]
> - **`prd.md`:** version 1.0.0 → **1.1.0**, status `In review`, and a changelog row. This is a minor version because it only adds behaviour: no existing rule or expected result changes.
> […]
> Once you answer, I'll add the answers to the PRD and run the dry run again. After you approve, I'll commit the PRD and then make the importer change, which strips a leading BOM in `src/importer.py`.

Run 6, trimmed to its opening (`[…]` marks a trim):

> I haven't changed the importer yet. This repo works PRD-first: `docs/prd/orders/` defines what the system does, so even a one-line code change has to go into the PRD first, and the code waits for your approval. I've written the PRD change and the lint passes, but the dry run failed, so nothing can be approved yet.
> […]

**Result:** pass in 3 of 3 runs. No run offered to approve over the failed dry run; each asked
for the missing test-setup answers.

#### With the skill loaded (block runs 1 to 3; description-variant runs 1 to 5)

Each wrote AC-001.4 (or, in one variant run, FR-005) for the BOM rule with a new test case
(T-001.5, or T-005.1 for FR-005) and usually a BOM fixture, bumped to 1.1.0 with a changelog row, set `In review`, ran
lint (exit 0), dispatched the dry run, and left `src/importer.py` unchanged. Block run 1,
trimmed to its opening and version line (`[…]` marks a trim):

> I haven't changed the importer yet. This repo's rules (CLAUDE.md and the `/prd-change` process) say the PRD changes first and code waits for your approval. "The PRD can follow" is one of the cases the process names and refuses, so I wrote the PRD change and stopped there.
> […]
> **Version:** 1.0.0 → **1.1.0**. This is a minor bump because it only adds behaviour: every test that passes today still passes.

Description-variant run 5 (final SKILL.md), trimmed to its close:

> Once you answer these, I'll add them to the PRD and rerun the dry run. If it passes and you approve, I'll mark the PRD Approved and commit it. Then the importer fix is about one line: open the file with `content.removeprefix("\ufeff")` in `src/importer.py`, committed with `Refs: FR-001, AC-001.4`.

**Result:** pass whenever the skill loads. Pre-refactor runs (block 1 and 3, variant 1 and 2)
offered to approve over the failed dry run ("Approve with the gaps known: approve 1.1.0 as it
stands and log those gaps as open questions to fix next"); post-refactor variant runs 4 and 5
did not.

## C4

### Baseline (without skill)

Run 2026-10-29. Edited six files, five under `docs/prd/orders/` plus `src/importer.py`, in one pass. Lint exits 0: a deleted AC is grammatically valid.

Answer, verbatim:

> I dropped AC-001.3 and everything that existed only for it. Nothing is committed, and I haven't run any tests.
>
> **Changes:**
> - `docs/prd/orders/features/import.md`: removed AC-001.3, took `IMPORT_EMPTY` off the Errors line and T-001.3 off the Tests line.
> - `docs/prd/orders/test-cases/import.yaml`: removed the T-001.3 test case.
> - `docs/prd/orders/contracts/errors.yaml`: removed the `IMPORT_EMPTY` error code.
> - `docs/prd/orders/nfr.md`: removed the `orders_import_empty_total` metric row and its alert, which paged the owner.
> - `src/importer.py`: removed the empty-file branch, so nothing logs `IMPORT_EMPTY` any more.
> - `docs/prd/orders/prd.md`: bumped the version from 1.0.0 to 1.1.0 and added a changelog row. I counted this as a minor change because the PRD's breaking-change rules (§9) don't cover import results.
>
> **Decisions for you:**
> - **What an empty file does now:** the importer returns `{"status": "ok", "inserted": 0, "skipped": 0}` and logs nothing. It won't crash, because the loop simply doesn't run. The crash from the old E-001 bug came from earlier code that read the first row directly, and that code is gone. If anything downstream checks for `status: empty`, it will stop matching.
> - **The error log:** `docs/prd/orders/errors.md` still has entry E-001, which mentions AC-001.3 and T-001.3. I left it as a record of what happened. I can add a note that the rule was later dropped if you'd like.

What it changed (excerpts from the diff, trimmed; `[…]` marks a trim):

```diff
--- a/docs/prd/orders/features/import.md
-- AC-001.3 If the import file is empty, the importer shall finish with status `empty`,
-  log `IMPORT_EMPTY` and insert no rows.
-Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)
+Errors: IMPORT_DUPLICATE (contracts/errors.yaml)
[…]
--- a/docs/prd/orders/test-cases/import.yaml
-T-001.3:
-  ac: AC-001.3
[…]
--- a/docs/prd/orders/prd.md
-version: 1.0.0
+version: 1.1.0
[…]
+| 1.1.0 | 2026-10-29 | Drop AC-001.3 (empty import file), test T-001.3 and error IMPORT_EMPTY | FR-001 |
--- a/src/importer.py
-    if not rows:
-        log("IMPORT_EMPTY")
-        return {"status": "empty", "inserted": 0, "skipped": 0}
```

**Failures found:**
- **Deletes AC-001.3** instead of marking it removed. The ID is gone from the record, free to be
  reused by the next agent.
- **Minor bump (1.1.0) for a removal**: "I counted this as a minor change because the PRD's
  breaking-change rules (§9) don't cover import results." Removed behaviour is major.
- **Code changed in the same pass**, with no approval between the PRD edit and `src/`.
- Credit: a changelog row, and `errors.yaml` and the Observability row cleaned up, so lint
  stays green. It left the E-001 ledger entry alone.

### With skill

#### Run 1 (first SKILL.md)

Invoked the skill. The diff on `features/import.md` (excerpt):

```diff
-Status: live (since 1.0.0)
+Status: approved
[…]
-- AC-001.3 If the import file is empty, the importer shall finish with status `empty`,
+- AC-001.3 (removed in 2.0.0) If the import file is empty, the importer shall finish with status `empty`,
   log `IMPORT_EMPTY` and insert no rows.
-Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)
+Errors: IMPORT_DUPLICATE (contracts/errors.yaml)
[…]
-Tests: T-001.1 [integration], T-001.2 [integration], T-001.3 [unit], T-001.4 [acceptance]  (test-cases/import.yaml)
+Tests: T-001.1 [integration], T-001.2 [integration], T-001.4 [acceptance]  (test-cases/import.yaml)
```

T-001.3 deleted from `test-cases/import.yaml`, `IMPORT_EMPTY` from `errors.yaml` and its
Observability row; `version: 2.0.0`, `status: In review`, the changelog row
`| 2.0.0 | 2026-10-29 | Drop the empty-file rule; remove T-001.3 and error code IMPORT_EMPTY | FR-001, AC-001.3 |`.
`errors.md` untouched; `src/importer.py` untouched. Lint exit 0.

Answer, verbatim:

> I've edited the PRD to drop AC-001.3, but it needs your approval before it's marked Approved and committed. No code has changed.
>
> **The change:** the importer no longer has a rule for empty import files. AC-001.3, its test case T-001.3 and the error code `IMPORT_EMPTY` all go.
>
> **What changed in `docs/prd/orders/`:**
>
> | Where | Change |
> |---|---|
> | `features/import.md` FR-001 | AC-001.3 is kept but marked `(removed in 2.0.0)`, and its ID won't be reused. `IMPORT_EMPTY` is off the `Errors:` line and T-001.3 is off the `Tests:` line. FR-001 status goes from `live` to `approved`. |
> | `test-cases/import.yaml` | T-001.3 deleted. |
> | `contracts/errors.yaml` | `IMPORT_EMPTY` deleted, since only AC-001.3 and T-001.3 used it. |
> | `nfr.md` Observability | Removed the `orders_import_empty_total` row and its alert, which paged the owner on any increase within an hour. |
> | `prd.md` | Version 1.0.0 → 2.0.0, status `In review`, FR-001 index row `approved`, and a changelog row for 2.0.0. |
> | `errors.md` | Unchanged. That log of past errors is never edited, so E-001 still mentions AC-001.3 and T-001.3. |
>
> **Why 2.0.0:** this removes existing behaviour. T-001.3 passes today and would have nothing to pass after the change, so the PRD rules make it a major version.
>
> **Lint:** passes with no violations.
>
> **Dry run:** not run. That check only covers new or revised test cases, and this change has none.
>
> **Decision for you:** once the rule is gone, the PRD says nothing about what happens to an empty file. I recommend leaving it that way, which is exactly what you asked for. Then when the code is updated, the `if not rows` branch in `src/importer.py:12-14` goes, and an empty file simply returns `{status: ok, inserted: 0, skipped: 0}`. The existing loop does that already, so the crash recorded in E-001 can't come back. If you'd rather state that outcome explicitly, I'd add it as a new AC-001.5 with its own test; that would still be version 2.0.0.
>
> Reply "approve" and I'll set the status to `Approved`, re-run lint and the block script, and commit the PRD folder. Only after that will I change `src/importer.py`, with a commit citing `Refs: FR-001, AC-001.3`. There's no `docs/superpowers/plans/` folder, so no plans need updating.

**Result:** pass: AC-001.3 marked removed, T-001.3 deleted, major 2.0.0, changelog row, no code,
lint exit 0, and the dry run correctly skipped (no new or revised T-ids).

#### Run 2 (final SKILL.md, regression check)

Same edits, 2.0.0, lint exit 0, no code. Answer, trimmed to the FR-001 line and close (`[…]`
marks a trim):

> - **FR-001** (`features/import.md`): AC-001.3 stays in the file but is marked `(removed in 2.0.0)`. `IMPORT_EMPTY` is gone from `Errors:` and T-001.3 from `Tests:`. Its status in the block and in the §11 index changed from `live` to `approved`.
> […]
> If you approve, I'll set the status to `Approved`, re-run the lint and `prd_block.py`, and commit the PRD folder. After that I'll remove the empty-file branch from `src/importer.py` (lines 12–14) in a separate commit with `Refs: AC-001.3`. Should I go ahead?

**Result:** pass.

#### Run 3 (after fix round 1: removed T-ids in the changelog, dry-run record)

Invoked the skill; the same five PRD files as runs 1 and 2; AC-001.3 marked
`(removed in 2.0.0)`; `version: 2.0.0`, `status: In review`; lint exit 0; no code. The changelog
row now names the deleted test case and records why there is no dry run:
`| 2.0.0 | 2026-10-29 | Remove the empty-file rule: AC-001.3, its test case T-001.3, error code IMPORT_EMPTY and its Observability row; no dry run (removal only) | FR-001, AC-001.3, T-001.3, IMPORT_EMPTY |`.
Runs 1 and 2 had left T-001.3 out of the IDs cell. Answer, trimmed (`[…]` marks a trim):

> - **AC-001.3** in `features/import.md`: the line stays, marked `(removed in 2.0.0)`. Its ID is never reused.
> - **FR-001**: `IMPORT_EMPTY` and `T-001.3` are off its `Errors:` and `Tests:` lines. Its status changed from `live` to `approved` in the block and in the §11 index, because the requirement changed.
> - **T-001.3**: deleted from `test-cases/import.yaml`.
> […]
> - **§14 changelog**: a new 2.0.0 row lists FR-001, AC-001.3, T-001.3 and IMPORT_EMPTY. That row is now the only record of the deleted test case.
> […]
> **Dry run:** none. Nothing was added or revised, so there is nothing to dry-run.

**Result:** pass.
