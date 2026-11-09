# prd-toolkit 0.8.4: README files and an Overview tab for each PRD — design

> **Date:** 2026-11-04
> **Author:** Ivan Histand & Claude Code
> **Status:** Approved by the owner 2026-11-04 (sections 1 to 15); section 16 approved in the brainstorm
> of 2026-11-07, the written text awaiting review
> **Extends:** `2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md` and the specs it extends,
> under `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this addendum and any of them disagree, this
> addendum wins for 0.8.4.
> **Needs:** 0.8.1's `prdlint/change.py` (the digest and the bump) on `main`, and 0.8.3 merged.
>
> **Revisions.**
> - Section 8's mermaid line (owner, 2026-11-08): the proof found that the Artifact viewer draws no
>   mermaid diagram on an HTML page, so the page shows the source everywhere. 0.8.4 ships as built,
>   with the text corrected; drawing the diagram moves to 0.8.5.
> - Section 16 and the scope (owner, 2026-11-07): the fixes from the 0.8.3 proof and its residuals
>   join 0.8.4 as section 16. The six deploy and pack items that section 16 held move to 0.8.5
>   (`2026-11-07-prd-toolkit-0.8.5-deploy-and-packs-design.md`), best practices to 0.8.6 and
>   conversion to 0.8.7. A removed block's §11 Since stays as 0.8.3 writes it: the `since` of its
>   `Status:` line, empty when that line has none.
> - Renumbered (owner, 2026-11-06): the fixes from the 0.8.2 proof are inserted as 0.8.3
>   (`2026-11-06-prd-toolkit-0.8.3-backlog-design.md`), so this release is 0.8.4, best practices 0.8.5
>   and conversion 0.8.6. The file was `2026-11-04-prd-toolkit-0.8.3-prd-readmes-design.md`; its
>   content is unchanged.
> - Sections 1, 2 and 7 to 15 (owner, 2026-11-04): the published page's Overview tab is folded in,
>   with §2's optional `Principles:` and `Getting started:` parts and one set of facts for the README
>   and the tab; the toolkit's own PRD gains both parts in the same `/prd-change` as its `lint-cli`
>   requirement.

## 1. Scope

A person who browses a repository the toolkit manages finds `docs/prd/` and `docs/prd/<slug>/` with
no explanation: a dozen Markdown and YAML files, IDs like `FR-013` and `T-004.3`, and nothing that
says what the folder is, whether to edit it, or how. 0.8.4 gives both folders a README.

A person who opens a page from `/prd-publish` meets the same gap one level up: a Business and a
Technical tab, each a deep dive, and nothing that says in one screen what the system is, what it
holds to, how it is built and where it stands. 0.8.4 gives the page an **Overview** tab, opened by
default. Both the README and the tab are assembled from the PRD's own sections, never from text
outside the PRD folder, so `prd.md` §2 gains two optional parts the format had no place for:
**Principles** and **Getting started**.

0.8.4 delivers:
- a managed block in `docs/prd/<slug>/README.md` and in `docs/prd/README.md`, written by
  `prd_block.py` beside the `CLAUDE.md` block (sections 3 and 4);
- the PRD folder's root `README.md` skipped by lint, the change digest, the bump and the tester
  (section 5), through a `lint-cli` change to the toolkit's own PRD;
- a stale-block check in `prd_hooks.py check --ci`, covering `CLAUDE.md` too (section 6);
- `prd_hooks.py install` refreshing the three blocks, so an upgrade writes the READMEs (section 6);
- the optional `Principles:` and `Getting started:` parts of §2 (section 7);
- the published page's Overview tab (section 8);
- one module that gathers the facts both the README and the tab show (section 9);
- the toolkit's own PRD with its principles and getting-started steps in §2 (section 10);
- ten fixes from the 0.8.3 proof and the residuals 0.8.3 parked, none of them in an adopted area
  (section 16).

**Success:** someone new who opens either folder on GitHub, or a published page, understands within
a minute what it is and how it is used, and neither README is ever stale on `main`.

### Decisions

| Decision | Choice |
|---|---|
| Who gets them | Every PRD the toolkit manages, through the same path as `CLAUDE.md`'s block. This repository is the first user |
| What the toolkit owns | A managed block between `<!-- prd-toolkit:start -->` and `<!-- prd-toolkit:end -->`; text outside the markers belongs to the owner and is never touched |
| The system's description | Quoted from the PRD: §2's first paragraph in the PRD's README, its first sentence in the parent's table. A better description is a better §2, through `/prd-change` |
| Staying current | The skills refresh it wherever `prd_block.py` already runs; `prd_hooks.py check --ci`, which the PR workflow runs, fails on a stale block. No pre-commit check: mid-change the version moves before step 5 refreshes the blocks |
| Architecture | `prd_block.py` writes all three blocks from three templates; one command, one `--check` |
| Where the overview goes on the page | Its own tab, first and opened by default. Not the top of the Business tab: engineers go straight to Technical and would miss it |
| The overview's source | The PRD only, as the publish rules require: §2, §4, §11 and the block statuses, `adoption.md`, `errors.md`, `links.md`. No Claude-written introduction; a better introduction is a better §2 |
| What the PRD lacked | Principles and getting-started steps: two optional labelled parts of §2, written like `Goals:` and `Personas:`, so no section is added or renumbered and no existing PRD breaks |
| Release vehicle | 0.8.4, after 0.8.3, with the Overview tab folded in because it shows the same facts as the README from the same sections, and the small fixes of section 16. The deploy and pack items move to 0.8.5, best practices to 0.8.6 and conversion to 0.8.7. The 0.8.0 retarget refusal names no release number from 0.8.2 on, so renumbering never again changes shipped text |

## 2. Components

| Path (under `prd-toolkit/`) | New or changed | Role |
|---|---|---|
| `scripts/prd_block.py` | changed | Writes and checks the `CLAUDE.md` block and the two README blocks |
| `templates/readme-prd.md`, `templates/readme-prds.md` | new | The two README blocks, with `{{slot}}` placeholders as `claude-block.md` has |
| `scripts/prdlint/model.py` | changed | Skips the PRD folder's root `README.md` (a `lint-cli` Boundary file: section 5) |
| `scripts/prdlint/rules/structure.py` | changed | Its raw-file scan skips the same file |
| `scripts/prdlint/change.py` (0.8.1) | changed | The digest and the bump skip it |
| `scripts/prdlint/hooks.py`, `scripts/prd_hooks.py` | changed | Vendors the two templates and writes `.prd-toolkit/HOMEPAGE`; `install` refreshes the three blocks; `check --ci` reports a stale block |
| `.claude-plugin/plugin.json` | changed | Gains `"homepage"`: the plugin's README on its repository |
| `skills/authoring-prds`, `adopting-prds`, `changing-prds`, `coordinating-prds` | changed | Stage the two READMEs with the PRD commit wherever they run `prd_block.py` |
| `skills/testing-from-prds/SKILL.md`, `agents/prd-tester.md` | changed | The README is a guide generated from the PRD, never a source for a test |
| `scripts/prdlint/overview.py` | new | The facts both the README and the Overview tab show (section 9) |
| `scripts/prdlint/publish.py`, `templates/publish/page.html` | changed | The Overview tab, first and checked by default; a mermaid fence as `<pre class="mermaid">` (section 8) |
| `references/prd-format.md`, `templates/prd/prd.md` | changed | §2's optional `Principles:` and `Getting started:` parts (section 7) |
| `references/languages/en.yaml`, `es.yaml` | changed | The tab's labels and the two parts' labels |
| `skills/authoring-prds/SKILL.md`, `skills/adopting-prds/SKILL.md` | changed | Phase 2 and the bootstrap offer the two parts; neither is ever required |
| `skills/publishing-prds/SKILL.md` | changed | Three tabs; the Overview needs no summary and gets none |
| `docs/prd/prd-toolkit/` (the toolkit's own PRD) | changed | The `lint-cli` requirement of section 5 and §2's two parts (section 10), in one `/prd-change` |
| `README.md`, version files | changed | The READMEs, the Overview tab, the upgrade note, the 0.8.4 changelog |

## 3. The PRD's README

`docs/prd/<slug>/README.md`. The block, every slot filled from the PRD:

```markdown
<!-- prd-toolkit:start -->
# {{slug}} — product requirements

This folder is the living PRD for **{{slug}}**: the requirements that say what it does, kept in
step with the code. The code implements this PRD, and a change in behaviour starts here, not in
the code. It is maintained with prd-toolkit, a Claude Code plugin{{parent_link}}.

Version {{version}} · {{status}} · Owner: {{owner}} · Updated {{updated}}

## What this PRD covers

{{summary}}

## Areas

{{areas}}

## What is in this folder

{{files}}
{{links}}
## Reading and changing it

- Read `prd.md`, then the area you care about. With the plugin: `/prd-status` for where every
  requirement stands, `/prd-context <area>` for one area, `/prd-publish` for a readable page.
- Don't edit these files by hand. A change in behaviour starts with `/prd-change` and is built
  with `/prd-build`; a bug starts with `/prd-error`. Lint and the git hooks check every commit.
<!-- prd-toolkit:end -->
```

| Slot | Value |
|---|---|
| `slug`, `version`, `status`, `owner`, `updated` | `prd.md` frontmatter; a missing key is `unknown` |
| `parent_link` | ` (see [../README.md](../README.md) to set it up)` when the parent README is written (section 4); empty otherwise |
| `summary` | §2's first paragraph, word for word, each line prefixed `> `. A §2 with no paragraph: `_No summary yet: prd.md §2 is empty._` |
| `areas` | A table `\| Area \| Adoption \| File \|`: one row per `features/*.md`, sorted, its Adoption the `adoption.md` state, or `-` with no `adoption.md`, its File a link |
| `files` | A table `\| Path \| Holds \|` with one row for each of `prd.md`, `features/`, `test-cases/`, `contracts/`, `testing.md`, `errors.md`, `operations.md`, `nfr.md`, `adoption.md`, `links.md` that exists, in that order, with the fixed text below |
| `links` | With a `links.md`: a `## Linked PRDs` section, lists **Upstreams** and **Consumers** from its tables, each location as recorded, a relative path as a link and a `<git URL>#<folder>` as code; empty otherwise |

The `files` texts are fixed:

| Path | Holds |
|---|---|
| `prd.md` | The overview: goals, glossary, architecture, the requirement index, open questions, changelog |
| `features/` | One file per area: requirements (`FR-nnn`) and their acceptance criteria (`AC-nnn.n`) |
| `test-cases/` | The test cases for each criterion (`T-nnn.n`), which the tests cite |
| `contracts/` | The interfaces the code must match: commands, configuration, schemas, APIs |
| `testing.md` | How the tests are run, at which level and gate |
| `errors.md` | The error ledger: every bug, its class and its fix (`E-nnn`) |
| `operations.md` | Environments and the deploy runbook |
| `nfr.md` | Non-functional requirements (`NFR-nnn`) |
| `adoption.md` | Which areas of the existing code are under this PRD, and their state |
| `links.md` | The PRDs whose contracts this one uses or provides |

Nothing in the block changes outside a PRD change: no requirement status, which moves during a build
and a deploy when `prd_block.py` does not run. `/prd-status` gives those.

## 4. The parent README

`docs/prd/README.md`, written only when the PRD folder's parent is named `prd`. A PRD kept elsewhere
gets its own README only; the script never writes a README in a folder that may belong to someone
else.

```markdown
<!-- prd-toolkit:start -->
# Product requirements

Each folder here is a living PRD: the requirements for one system in this repository, kept in
step with its code. Code implements its PRD; a change in behaviour starts in the PRD.

{{prds}}

## How it works

- Each area of a system has requirements (`FR-nnn`); each requirement has acceptance criteria
  (`AC-nnn.n`), and each criterion has test cases (`T-nnn.n`).
- Tests cite the test cases they prove, and commits cite the requirements they implement
  (`Refs: FR-012`), so a change can be traced from the PRD to the code and back.
- Bugs are recorded in each PRD's `errors.md` before they are fixed.
- Lint, the git hooks and CI check that the PRD, the tests and the code stay in step.

## Getting started

- Install the prd-toolkit plugin for Claude Code: {{homepage}}
- Once per clone: `uv run --script .prd-toolkit/prd_hooks.py install docs/prd/<slug>`
- Then see each PRD's README.
<!-- prd-toolkit:end -->
```

- `prds` is a table `| PRD | Version | Status | Covers |`, rebuilt on each run from every folder beside
  the PRD that holds a `prd.md`, sorted by folder name. Covers is §2's first sentence (up to the first
  `. `, `? ` or `! `, or the paragraph's end), or `-`. A sibling whose `prd.md` does not load is the row
  `| <slug> | - | could not be read | - |`, with a stderr note, and the run still exits 0. A folder
  with no `prd.md` is not listed.
- `homepage` is `plugin.json`'s `homepage`. Vendoring writes it to `.prd-toolkit/HOMEPAGE` (one line,
  as `.prd-toolkit/VERSION` holds the version; `VERSION` itself is unchanged), so a vendored run and a
  plugin run write the same text. A wrapper plugin's own `homepage` shows instead. With no `homepage`,
  the line reads `Install the prd-toolkit plugin for Claude Code.`
- The parent shows no links: it describes this repository's folders, and a link usually points into
  another repository.

## 5. What skips the README

The PRD folder's root `README.md` is generated from the PRD, so nothing that reads the PRD as its
source reads it. Only that one file is skipped; any other README (the template's
`contracts/dependencies/README.md`) is read as today.

| Reader | Change |
|---|---|
| Lint: `prdlint/model.py` (every `.md`) and `rules/structure.py` (the raw scan) | Skip it |
| `prdlint/change.py`: the digest and the bump | Skip it, as `.prd-review.json` |
| The tester: `testing-from-prds`, `agents/prd-tester.md` | One rule: the README is a guide generated from the PRD, never a source for a test or a question |
| `prd_publish.py`, `prd_context.py`, `prd_trace.py` | No change; a test pins that each ignores it |

**The toolkit's own PRD changes first.** `prdlint/model.py` is in the adopted `lint-cli` area's
Boundary, and the commit hook refuses a change to it without a requirement ID. The release begins
with `/prd-change` (section 10): on `lint-cli`, a requirement that lint ignores the PRD folder's root
`README.md`, with its test case. The owner approves it before any code, and `/prd-build` builds it,
as 0.8.0 and 0.8.1 did.

## 6. Writing, checking and upgrading

**Writing.** `prd_block.py <prd dir>` writes the three blocks. Into a file that exists without
markers, the block goes at the top, then a blank line, then the existing text unchanged; a refresh
rewrites only the text between the markers. Two start markers, or unbalanced markers, exit 2, as for
`CLAUDE.md` today; markers inside a closed code fence are not markers.

**Where it runs.** Unchanged: authoring approval, adoption, `/prd-change` step 5 and the change-set
close. Each of those skills stages the two READMEs with `CLAUDE.md` and the PRD folder.

**Checking.** `prd_block.py --check <prd dir>` exits 1 and prints `stale: <file>` for each block that
differs from what it would write now, 0 when all three are current. `prd_hooks.py check --ci` runs
the same check and prints `stale: <file>; run prd_block.py docs/prd/<slug>`. The PR workflow already
runs `check --ci`, so a stale README fails the PR; `CLAUDE.md`, which nothing checked before, is
covered too.

**Upgrading.** `prd_hooks.py install`, the documented upgrade step, refreshes the three blocks after
it vendors the copy (new in 0.8.4: before, it only vendored the block template). An upgrade
therefore writes both READMEs in the same commit as the vendored copy, and the next PR does not fail
the new check.

**A known limit.** Two branches that each change a different PRD both rewrite the parent's table, so
their merge can conflict there. The fix is to rerun `prd_block.py`, never a hand edit; the check
message says which command.

## 7. Principles and Getting started in §2

`prd.md` §2 may hold two more labelled parts, beside `Goals:`, `Personas:` and `Out of scope:`:

```markdown
Principles:

- **<name>.** <one or two sentences>

Getting started:

1. <a step a new user takes>
```

- A part starts at a line that begins with its label (`Principles:` or `Getting started:`, or the
  PRD language's label from `references/languages/<code>.yaml`: `es` is `Principios:` and
  `Primeros pasos:`) and runs to the next labelled line of §2 (`Goals:`, `Personas:`,
  `Out of scope:`, `Principles:`, `Getting started:`) or the end of §2. Text after the label on its
  own line belongs to the part.
- Both are optional and free Markdown. Lint checks nothing new: the `sections` rule reads headings
  only, and the prose rules already read §2.
- The template's §2 gains one HTML comment naming the two parts, and no marker: a PRD without them
  is complete.
- Authoring phase 2 and the adoption bootstrap offer to draft them from what the user has said; the
  user's words decide them like any other §2 text. Neither skill requires them.

## 8. The published Overview tab

`prd_publish.py render` writes three tabs: **Overview**, checked by default, then Business and
Technical, unchanged. The tab is CSS-only, as the other two, and loads nothing. Its parts, in order,
each from the PRD and each left out when its source is empty:

| Part | Source |
|---|---|
| The line `<version> · <status> · Owner: <owner> · Updated <updated>` | `prd.md` frontmatter |
| **What it is** | §2's first paragraph (section 9) |
| **Principles** | §2's `Principles:` part, rendered as Markdown |
| **Architecture** | §4, rendered as Markdown |
| **Areas** | A table `\| Area \| Adoption \| Requirements \|`: one row per `features/*.md`, sorted; Adoption from `adoption.md` (`-` without one); Requirements the area's FR and NFR blocks counted by `Status:`, as `3 verified, 1 approved`, in the order `live`, `verified`, `built`, `approved`, `as-built`, and `removed` left out |
| **Open errors** | The count of open `errors.md` entries, as `2 open errors; the Technical tab lists them`, or `No open errors.` |
| **Linked PRDs** | `links.md`'s Upstreams and Consumers, as the README shows them |
| **Getting started** | §2's `Getting started:` part, rendered as Markdown |
| The line `A snapshot of the PRD at version <version>. The PRD in the repository is the authority.` | fixed, in the PRD's language |

- **Mermaid.** A ```` ```mermaid ```` fence anywhere on the page, the Technical tab's §4 included,
  renders as `<pre class="mermaid">` holding the escaped source. The page still loads nothing, and
  every viewer shows the source: the Artifact viewer runs no mermaid on an HTML page (the 0.8.4
  proof, 2026-11-08). Drawing the diagram is 0.8.5's item 9.
- The Overview takes no summary: `--summaries` keys are areas, and the tab restates nothing.
- Every label is a language-table key (`overview`, `what_it_is`, `principles`, `areas`,
  `open_errors`, `linked_prds`, `getting_started`, `snapshot_line`), with `en` and `es` values; a key
  a table lacks falls back to `en`, as today.

## 9. One set of facts

`prdlint/overview.py` gathers what the README blocks and the Overview tab show, so the two never
disagree:

- `overview.facts(prd) -> Facts`: slug, version, status, owner, updated; `summary` (§2's first
  paragraph) and `first_sentence`; `principles` and `getting_started` (section 7's parts, or `None`);
  `areas` (name, file, adoption state, status counts); `open_errors`; `links` (upstreams,
  consumers); `files` (which of section 3's paths exist).
- **§2's first paragraph** is the first run of non-blank lines in §2 after HTML comments are
  removed, ending at a blank line or a heading, and never a paragraph that starts with a labelled
  part (`Goals:` and the rest). With none, `summary` is `None`.
- `prd_block.py` fills the README slots from `Facts`; `publish.py` fills the tab from it. The
  README shows no status counts (section 3); the page, a snapshot, does.
- `summary_paragraph` and `first_sentence` live here, not in `prd_block.py`, so §3's `summary` slot
  and the tab's What it is are one function.

## 10. The toolkit's own PRD

One `/prd-change` on the toolkit's own PRD carries both of its 0.8.4 changes, before any code:

- the `lint-cli` requirement of section 5;
- §2's `Principles:` part (the seven principles of the design binder's Overview: the PRD is the
  authority; spec-first, enforced; black-box testable; Error-Driven Development; the owner's word
  decides; mechanical gates before judgement; the toolkit stays generic) and its `Getting started:`
  part (install the plugin; `/prd-new` or `/prd-adopt`; install the hooks once per clone;
  `/prd-change` then `/prd-build`, and `/prd-error` for a bug), in words the owner approves.

The lint requirement adds behaviour, so the change is a minor bump. The owner approves it as one
change, and `/prd-build` builds the lint requirement; §2's parts need no build.

## 11. Changes to the 0.8.2 spec and the umbrella

- **The umbrella's §4:** 0.8.4 is this release, 0.8.5 the deploy and pack items, 0.8.6 best
  practices, 0.8.7 conversion, with their "Needs" columns moved; a Revisions line records it.
- **The 0.8.2 spec and plan:** the retarget refusal becomes
  `retargeting an area is a conversion, which a later prd-toolkit release brings`, in the skill (both
  places), its test pin and the eval's expected text, in place of the text naming 0.8.4. Their
  Revisions record it.

## 12. Testing the toolkit

Fixture PRDs `greet`, `orders` and `notes`.

- **The PRD's README:** each slot of section 3, including a §2 paragraph over several lines, the areas
  from `adoption.md` and without it, only existing files listed, `links.md` with a relative path and a
  git URL, an empty §2.
- **The parent:** two PRDs sorted; a sibling that does not load (the row, the stderr note, exit 0); a
  folder with no `prd.md` absent; no parent written when the folder is not named `prd`; `homepage`
  from a plugin run and from a vendored run equal.
- **Merging:** an existing README without markers keeps its text byte for byte below the block; text
  outside the markers survives a refresh; two start markers exit 2; fenced markers ignored.
- **Checking:** `--check` names each stale file and exits 1, and exits 0 when current; `prd_hooks.py
  check --ci` fails on a stale README and on a stale `CLAUDE.md` block, and passes when refreshed;
  `install` writes the three blocks.
- **The skips:** a root README holding a vague word, `FR-999` and `[NEEDS CLARIFICATION: x]` gives no
  lint finding, while `contracts/dependencies/README.md` is still linted; a README edit changes
  neither the digest nor the bump; publish, context and trace ignore it.
- **The skills:** each skill that runs `prd_block.py` stages both READMEs; the tester rule is present.
  One eval, written with `superpowers:writing-skills`: the tester, given a README that states a
  behaviour the feature file does not, never cites it or writes a test from it.
- **§2's parts:** each label found at the start of a line and ended by the next labelled line or the
  end of §2; the `es` labels; text on the label's own line kept; a §2 that opens with `Goals:` has no
  summary; a template comment before the summary is skipped.
- **The Overview tab:** checked by default, and the Business and Technical tabs unchanged otherwise;
  each part of section 8 present from a fixture that has its source and absent from one that lacks
  it; the status counts in their order with `removed` left out; the open-error line in both forms;
  every label from the `es` table on a Spanish fixture; a mermaid fence as `<pre class="mermaid">`
  with `<` and `&` escaped, on both tabs; the page still loads nothing (no `<script`, `<link`,
  `@import`, `url(`). The golden page `tests/fixtures/publish/orders.html` is regenerated once, and its
  diff reviewed as the change.
- **One set of facts:** the README's slots and the tab's parts on one fixture name the same version,
  summary and areas.
- **The skills:** `publishing-prds` names three tabs and says the Overview takes no summary; the
  authoring and adoption texts offer the two parts and never require them.

## 13. Proof

1. `prd_block.py docs/prd/prd-toolkit` writes `docs/prd/README.md` and `docs/prd/prd-toolkit/README.md`
   in this repository, and the PR's CI passes.
2. One block made stale on purpose fails CI with the fix command; the fix passes it.
3. The owner reads both files on GitHub and confirms they explain the folders to someone new.
4. `/prd-publish` on the toolkit's own PRD opens on the Overview tab, with its principles, its
   architecture diagram drawn, its one adopted area and its getting-started steps. Republished into
   the design artifact's PRD page, it replaces the 2.1.0 snapshot there; the owner confirms it.
5. Three of section 16's fixes on this repository: the build's own `.prd-toolkit/` refresh passes
   `prd_build_check.py --diff` with exit 0 (fix 6); the tester, dispatched for one T-id, runs its one
   test file under the harness's `uv run --directory` and finds the citing tests with Bash `grep`
   (fixes 2 and 3).

## 14. Upgrade

- A repository upgraded with `prd_hooks.py install` gets both READMEs and a current `CLAUDE.md` block
  in that commit.
- A repository that hand-edited its `CLAUDE.md` block fails `check --ci` until it reruns
  `prd_block.py`; the changelog names this as the one thing to watch for.
- A published page gains its Overview tab on the next `/prd-publish`; a PRD with no `Principles:` or
  `Getting started:` part gets the tab without those two parts, and nothing else changes.

## 15. Out of scope

- A README in any other folder of the PRD (`features/`, `contracts/` and so on).
- A Claude-written description or introduction, in the README or on the Overview tab; the
  description is the PRD's §2.
- Principles or getting-started steps as required parts, or as numbered sections of `prd.md`.
- Requirement statuses in the README; `/prd-status` gives them.
- More than one PRD in `CLAUDE.md`'s block.

## 16. Fixes from the 0.8.3 proof

The E-007 proof (PR #18) ran one defect through the toolkit's own PRD and found three gaps; 0.8.3
parked six residuals; one message dates from 0.8.1. None of them is in an adopted area (only
`lint-cli` is), so each is built from this spec and its commits carry
`Refs: none (no behaviour change)`, as 0.8.3's were. Fix 8 edits the PRD, through Task 1's
`/prd-change`. Every fix is test-first: its test fails before the change.

1. **A regression marker comes off with its symptom.** `running-a-build.md` says to remove a
   regression case's `known-failing: E-nnn` line "and no other test-case line". Lint then fails
   `test-refs: T-006.4: symptom: needs known-failing: on the same case`, so the E-007 build removed
   the `symptom:` lines as well, outside the procedure. Fix: both removals (step 4's deploy-gate
   lines and step 5's build-gate and unit lines) remove the case's `known-failing: E-nnn` line and
   its `symptom:` line when it has one, and no other test-case line. The caller's Red Flags in
   `building-from-prds/SKILL.md` say the same. Test: a skill-text pin on both steps and the Red
   Flag.

2. **A single test file under `uv run --directory`.** The tester's guard checks a path argument
   after a harness command from the hook's `cwd`, the worktree root. The toolkit's harness is
   `uv run --directory prd-toolkit pytest -q tests/prd`, so pytest reads the path from
   `prd-toolkit/` and the guard from the root: `… tests/prd/test_x.py` is refused, though it names a
   file under a test root. Fix: when the matched harness command holds uv's `--directory <d>` (or
   `--directory=<d>`), `_check_harness_args` resolves each path argument from `<d>`, itself resolved
   from `cwd`. Every other check stands: the resolved path must be inside a write root, and a glob
   is refused. Tests: that command with `tests/prd/test_x.py` is allowed; with
   `../prd-toolkit/scripts/prd_lint.py` and with `tests/prd/*.py` it is refused; a harness without
   `--directory` resolves from `cwd` as before.

3. **Searching without a Grep tool.** `prd-tester` lists Read, Glob and Grep, but a Claude Code
   build that exposes no Grep tool gives it none, and the skill and the guard bar Bash `grep`. The
   E-007 tester opened test files one by one to find the citing tests. Fix (owner, 2026-11-07): the
   guard accepts a Bash `grep` segment whose every file operand is readable (the PRD folder, the
   test roots, the scratchpad):
   - its options come from one list: `-r`, `-n`, `-l`, `-L`, `-c`, `-i`, `-w`, `-x`, `-v`, `-o`,
     `-q`, `-s`, `-H`, `-h`, `-E`, `-F`, `-e <pattern>`, `-f <file>`, `-m <n>`, `-A <n>`, `-B <n>`,
     `-C <n>`, `--include=<glob>`, `--exclude=<glob>`, and short flags from the list clustered
     (`-rn`). Any other option is refused, `-R` and `--dereference-recursive` among them, so a
     symbolic link inside a root is never followed out of it;
   - the pattern is the first operand, unless an `-e` or `-f` gives it; `-f`'s file must be readable;
   - at least one file operand, none holding a glob character, each resolved from `cwd` and readable.
   The skill's rule 6 and the agent's text become: search with the Grep tool, or, when there is
   none, with Bash `grep` naming each path; `cat`, `head`, `sed` and `find` stay barred. Tests:
   `grep -rn '@prd T-006' prd-toolkit/tests/prd` is allowed; `grep -R …`, `grep -rn x .` from a root
   above the test roots, `grep x prd-toolkit/scripts/prd_lint.py`, `grep x 'tests/*.py'`, `grep x`
   with no path and `grep -f prd-toolkit/scripts/x y` are refused; a skill-text pin on the rule.

4. **`_last_commit` reads a path as a pathspec.** `buildcheck._last_commit` runs
   `git log -1 -- <path>`, so a citing test whose name holds `[`, `*` or `?` is read as a glob and
   can match another file's commits. Fix: `git --literal-pathspecs log -1 -- <path>`. Test: with
   `tests/test_x.py` committed after `tests/test_[x].py`, `--stale` judges `tests/test_[x].py` by its
   own last commit.

5. **`_contract_ids` keeps IDs of one PRD.** 0.8.3's (j) says a cited ID is added when it is a block
   in either PRD, the base or the working tree. `change._contract_ids` keeps only the blocks of the
   PRD it reads the item from. Fix: the set it filters against is the union of both PRDs' blocks.
   Test: a changed contract item that cites an FR the same change removes lists that FR in the §14
   IDs cell.

6. **`--diff`'s refresh check.** `buildcheck.refresh_differences` rebuilds the expected
   `.prd-toolkit/` from `git archive <head>`, untarred in a temporary directory. Four faults:
   - `git archive` honours `export-ignore` and `export-subst`, so a repository that sets either on a
     plugin file vendors a different tree from the one the builder ran `vendor` on;
   - the archive is held in memory whole;
   - only bytes are compared, so a vendored file whose executable bit changed passes;
   - a `subprocess.TimeoutExpired` escapes as an internal error, and a failing `vendor` reads
     `vendor at <sha> failed: failed: …` when its own line starts `failed:`.
   Fix: check `<head>` out into the temporary directory through a temporary index
   (`GIT_INDEX_FILE` in that directory, `git read-tree <head>`, then
   `git checkout-index -a --prefix=<dir>/`), which applies no export attribute and streams to disk;
   compare each path's bytes and executable bit, a vendored file's from its mode on disk and a
   committed one's from `ls-tree` (`100755` or `100644`); every subprocess the check runs that times
   out raises a tool error, `<command> timed out after <n> s`; a failing vendor reads
   `vendor at <sha>: <its first line>`. Tests: an `export-ignore` on a vendored plugin file gives
   exit 0 for an exact refresh; a committed `.prd-toolkit/` file made executable is reported; a
   timeout (a stub `git` that sleeps) gives exit 2 with that line and no traceback; the vendor
   message.

7. **A corrupt deploy run log hides its gate.** `gates._deploy_step` skips a run log it cannot read,
   so the gate leaves the list, and the inbox, which still shows the card it loaded, gets a 409 when
   the owner answers it. Fix: such a log gives a gate `deploy-step:<run id>:unreadable`, titled
   `run log <run id> could not be read`, whose question is the reason (its first line). Answering it
   is refused with `refused: run log <run id> could not be read: <reason>`; the inbox shows the
   reason and no answer controls. Tests: a log with a bad JSON line is listed with that title;
   `prd_gates.py answer` on it exits 1 with that line; a readable log is unchanged.

8. **Scripts in no area.** Thirteen scripts are in no Boundary of the toolkit's `adoption.md`, so no
   area will ever adopt them. Fix: four `not started` rows, added in Task 1's `/prd-change`:
   - `gates`: `prd_gates.py`, `prdlint/gates.py`, `prdlint/formserver.py`, `prd_confirm.py`,
     `prdlint/confirm.py`;
   - `change`: `prd_change.py`, `prdlint/change.py`, `prdlint/change_approve.py`;
   - `judge`: `prd_judge.py`, `prdlint/judge.py`;
   - `packs`: `prdlint/packs.py`, `prdlint/languages.py`, `prdlint/rules/packs.py`.
   0.8.4's new `prdlint/overview.py` and the two README templates join the `status` row, beside
   `prd_block.py`. A `not started` row changes no behaviour and no commit rule. Test: a repository
   test that every `prd-toolkit/scripts/**/*.py` is named in exactly one row. Adopting `build-check`
   is a later release.

9. **A pack validator's failure says only its exit.** `contracts-valid` prints the first non-blank
   stderr line of a failing validator, else `validator failed: exit <n>`, so a validator that
   reports on stdout says nothing useful. Fix: the first non-blank stderr line, else the first
   non-blank stdout line, else `exit <n>`. Test: a stub validator that prints to stdout and exits 1
   gives `validator failed: <that line>`.

10. **The E-007 fix's release.** PR #18 changed lint's behaviour (E-007, PRD 5.0.0) after 0.8.3
    shipped, with no version bump; its line sits in the 0.8.3 changelog. The 0.8.4 entry says so:
    the fix first ships to installs in 0.8.4.

**Closed with no change.** A removed block's §11 Since (0.8.3's residual): it stays the `since` of
the block's `Status:` line, empty for a bare `removed` (owner, 2026-11-07). `changing-prds` writes
`removed (since X.Y.Z)`, so in use the cell holds the removal version.

**Moved to 0.8.5:** the six deploy and pack items this section held, and two later-release
candidates: `prd_context` judging STALE by the cited line's text, and `--diff` checking that each
SOURCES line falls inside the builder's hunks.
