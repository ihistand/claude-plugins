# prd-toolkit 0.8.3: README files for the PRD folders — design

> **Date:** 2026-11-04
> **Author:** Ivan Histand & Claude Code
> **Status:** Draft, awaiting review
> **Extends:** `2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md` and the specs it extends,
> under `2026-11-03-prd-toolkit-0.8-umbrella.md`. Where this addendum and any of them disagree, this
> addendum wins for 0.8.3.
> **Needs:** 0.8.1's `prdlint/change.py` (the digest and the bump) on `main`, and 0.8.2 merged.

## 1. Scope

A person who browses a repository the toolkit manages finds `docs/prd/` and `docs/prd/<slug>/` with
no explanation: a dozen Markdown and YAML files, IDs like `FR-013` and `T-004.3`, and nothing that
says what the folder is, whether to edit it, or how. 0.8.3 gives both folders a README.

0.8.3 delivers:
- a managed block in `docs/prd/<slug>/README.md` and in `docs/prd/README.md`, written by
  `prd_block.py` beside the `CLAUDE.md` block (sections 3 and 4);
- the PRD folder's root `README.md` skipped by lint, the change digest, the bump and the tester
  (section 5), through a `lint-cli` change to the toolkit's own PRD;
- a stale-block check in `prd_hooks.py check --ci`, covering `CLAUDE.md` too (section 6);
- `prd_hooks.py install` refreshing the three blocks, so an upgrade writes the READMEs (section 6).

**Success:** someone new who opens either folder on GitHub understands within a minute what it is
and how it is used, and neither README is ever stale on `main`.

### Decisions

| Decision | Choice |
|---|---|
| Who gets them | Every PRD the toolkit manages, through the same path as `CLAUDE.md`'s block. This repository is the first user |
| What the toolkit owns | A managed block between `<!-- prd-toolkit:start -->` and `<!-- prd-toolkit:end -->`; text outside the markers belongs to the owner and is never touched |
| The system's description | Quoted from the PRD: §2's first paragraph in the PRD's README, its first sentence in the parent's table. A better description is a better §2, through `/prd-change` |
| Staying current | The skills refresh it wherever `prd_block.py` already runs; `prd_hooks.py check --ci`, which the PR workflow runs, fails on a stale block. No pre-commit check: mid-change the version moves before step 5 refreshes the blocks |
| Architecture | `prd_block.py` writes all three blocks from three templates; one command, one `--check` |
| Release vehicle | 0.8.3, after 0.8.2. Best practices move to 0.8.4 and conversion to 0.8.5. The 0.8.0 retarget refusal names no release number from 0.8.2 on, so renumbering never again changes shipped text |

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
| `docs/prd/prd-toolkit/` (the toolkit's own PRD) | changed | The `lint-cli` requirement of section 5, through `/prd-change` |
| `README.md`, version files | changed | The READMEs, the upgrade note, the 0.8.3 changelog |

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
with `/prd-change` on `lint-cli`: a requirement that lint ignores the PRD folder's root `README.md`,
with its test case. The owner approves it before any code, and `/prd-build` builds it, as 0.8.0 and
0.8.1 did.

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
it vendors the copy (new in 0.8.3: before, it only vendored the block template). An upgrade
therefore writes both READMEs in the same commit as the vendored copy, and the next PR does not fail
the new check.

**A known limit.** Two branches that each change a different PRD both rewrite the parent's table, so
their merge can conflict there. The fix is to rerun `prd_block.py`, never a hand edit; the check
message says which command.

## 7. Changes to the 0.8.2 spec and the umbrella

- **The umbrella's §4:** 0.8.3 is this release, 0.8.4 best practices, 0.8.5 conversion, with their
  "Needs" columns moved; a Revisions line records it.
- **The 0.8.2 spec and plan:** the retarget refusal becomes
  `retargeting an area is a conversion, which a later prd-toolkit release brings`, in the skill (both
  places), its test pin and the eval's expected text, in place of the text naming 0.8.4. Their
  Revisions record it.

## 8. Testing the toolkit

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

## 9. Proof

1. `prd_block.py docs/prd/prd-toolkit` writes `docs/prd/README.md` and `docs/prd/prd-toolkit/README.md`
   in this repository, and the PR's CI passes.
2. One block made stale on purpose fails CI with the fix command; the fix passes it.
3. The owner reads both files on GitHub and confirms they explain the folders to someone new.

## 10. Upgrade

- A repository upgraded with `prd_hooks.py install` gets both READMEs and a current `CLAUDE.md` block
  in that commit.
- A repository that hand-edited its `CLAUDE.md` block fails `check --ci` until it reruns
  `prd_block.py`; the changelog names this as the one thing to watch for.

## 11. Out of scope

- A README in any other folder of the PRD (`features/`, `contracts/` and so on).
- A Claude-written description; the description is the PRD's §2.
- Requirement statuses in the README; `/prd-status` gives them.
- More than one PRD in `CLAUDE.md`'s block.
