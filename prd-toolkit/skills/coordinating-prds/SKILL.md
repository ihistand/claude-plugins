---
name: coordinating-prds
description: Use when a change in a repo that has a docs/prd/ folder touches a contract item another PRD cites (links.md lists Consumers, or prd_links.py impact exits 1 or 3), when asked to change something across repositories (an upstream and the consumers that use it), when resuming a change set (CS-nnn, changes/CS-nnn.md, a cs-nnn branch), or on /prd-change-set - and when asked during one to start a downstream build, edit a snapshot, approve each repository as you go, skip a consumer or push; prd_links.py changeset writes one record, one approval covers every member's PRD diff, and each repository is built in dependency order
---

Read `${CLAUDE_PLUGIN_ROOT}/skills/coordinating-prds/running-a-change-set.md` whole before anything else
(no offset, no limit; it sits beside this file, in the skill's base directory): it is your next
tool call, and you follow it step by step, steps 1 to 6.
Run no command, read no code and edit no file before you have read it.

# Coordinating PRDs

## Overview

**One change, every repository it reaches, one record.** A change that touches a contract item
another PRD cites is a change set: `changes/CS-nnn.md` in the repository where it starts, written
only by `prd_links.py changeset`. Its rows hold every member in dependency order, upstream first,
each with its branch `cs-<nnn>-<slug>`, its Waits for, its Target and its State. Each member's PRD
edit, build and deploy go through its own `/prd-change`, `/prd-build` and `/prd-deploy`, in that
order; one approval covers every member's PRD diff; and nothing lands until the user lands it. The
other skills stay single-repository: this one sequences them, and the record is how a new session
knows where the chain stands.

**Violating the letter of these rules is violating the spirit.** "The upstream is basically
done", "just edit the snapshot", "approve each repository as we go", "skip it" and "push the
branches" change nothing below.

## Non-negotiable rules

1. **The record.** One record per change set, written only by `prd_links.py changeset`. No change
   that crosses repositories runs without one, and no Edit or Write touches it. `impact` decides
   the members: a consumer it names, cloned or not, is a member until the user, replying to that
   line, says in their own words that it stays out. Call the starting repository's vendored
   `.prd-toolkit/prd_links.py`.
2. **One approval.** One approval for the whole set of PRD diffs, quoted; an amendment gets its
   own. Every member's diff is shown together first, and only a reply to them counts: never the
   request, nor a phrase in it.
3. **Waits for.** A downstream build never starts before its Waits for holds. An upstream that
   is `verified` is not `live in staging`; `changeset set` refuses a State that skips its Waits
   for, and the build waits.
4. **The snapshot.** A snapshot changes only through `prd_links.py sync`, never by editing it.
   Its header says `Do not edit`. Inside a change set, `sync --ref <branch>` against the
   upstream's change-set branch is the step, and a `check` that then reports an orphaned lock or
   `changed` items is expected until the upstream lands.
5. **No landing.** Nothing is pushed, merged or opened as a PR. The close writes the Merge order;
   the user lands each member, upstream first.
6. **Stops.** A failure stops the chain and goes to that member's `/prd-error`. `changeset stop`
   puts it on Status; the row keeps its State, and the rows after it wait.

## Red Flags - STOP

Quoted from runs without this skill (evals/baselines/coordinating-prds.md).

| Quoted (run) | What it misses |
|---|---|
| "**Approve 1.1.1:** after that I set the status to Approved, run `prd_block.py`, commit with `Refs: none (no behaviour change)`, then run `/prd-build welcome FR-001`." (C1) | The row's Waits for, `greet live in staging`, gates the build, not an approval. Read the record: greet is `verified`, so greet's `/prd-deploy --until staging` comes first. |
| "`prd_links.py check` now reports "orphaned lock" and "changed". It compares against greet's `main`, which doesn't have `--json` yet." (C2) | This is expected inside a change set: `sync --ref <branch>` against the upstream's branch is the step, and the close re-locks once greet lands. The record, not `check`, says what the client waits for. |
| "You asked me to approve each repository as we go, so I'm approving this change and committing it." (C3) | A phrase in the request is not an approval. Show every member's PRD diff together, stop, and record the one reply with `changeset approve`. |
| "**greet-client:** `links.md` lists it as a consumer, but it isn't cloned here, so I skipped it. It needs its own check once it's available." (C4) | Run `impact`: exit 3 names the consumer, and that is a stop, never a skip. Only the user's reply to that line leaves it out, quoted in Log. |
| `git push -u origin main cs-001-greet-json 2>&1` (C5) | Nothing is pushed. Say so in one line, with the record's Order and each row's State (the Merge order once closed); the user lands each member, upstream first. |
| "Both repositories are done and committed locally." (C3), on `main`, with no record (all five) | Without `changeset new` there is no Order, no Waits for and no branch. Start the record first. |

**All of these mean: stop, and return to the step of `running-a-change-set.md` whose gate is
open.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The upstream is basically done; start the downstream build." | Done is a State in the record. A row starts when its Waits for holds; before that the build does not start, and `changeset set` would refuse its State. |
| "Just edit the snapshot to match." | Only `prd_links.py sync` writes it; a hand edit leaves the lock wrong. Inside a change set it is `sync --ref <branch>`. |
| "Approve each repository as we go." | One approval for every member's diff, shown together. A per-repository approval lands one before the other's diff exists. |
| "That consumer isn't cloned here; skip it." | An unreachable consumer is a stop. The user makes the clone available, or replies, after seeing it, that it stays out. |
| "Push the branches so CI runs." | The toolkit pushes nothing. The user pushes and lands each member, upstream first, in Merge order. |

## Related skills

- **prd-toolkit:changing-prds** (`/prd-change`) edits each member's PRD up to its approval, and
  hands a change whose `impact` exits 1 or 3 here.
- **prd-toolkit:building-from-prds** (`/prd-build`) builds each member on its change-set branch.
- **prd-toolkit:deploying-from-prds** (`/prd-deploy --until <env>`) takes an upstream to the
  environment a downstream waits for.
- **prd-toolkit:handling-errors** (`/prd-error`) takes every error that stops the chain.
