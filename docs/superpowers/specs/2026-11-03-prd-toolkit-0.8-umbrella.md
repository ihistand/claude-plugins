# prd-toolkit 0.8: targets, packs, best practices and conversion — umbrella

> **Date:** 2026-11-03
> **Author:** Ivan Histand & Claude Code
> **Status:** Approved by the owner 2026-11-03
> **Extends:** `2026-10-29-prd-toolkit-design.md` (the base spec) and the 0.2 to 0.7 addenda
> (`2026-11-02-prd-toolkit-0.7-design.md` last).
> **Governs:** the 0.8.0 to 0.8.6 specs. Each sub-release has its own spec, plan, build and
> acceptance record; where one of them and this note disagree, the sub-release spec wins for that
> release and records the change in its Revisions note.

> **Revisions.**
> - §4 (owner, 2026-11-03): a machine interface for clients other than Claude Code (JSON output, change
>   bookkeeping as a script, one way to list and answer pending human decisions) is inserted as 0.8.1.
>   Best practices move to 0.8.2 and conversion to 0.8.3; their content is unchanged.
> - §4 (owner, 2026-11-04): a local decision inbox over 0.8.1's gates is inserted as 0.8.2
>   (`2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md`). Best practices move to 0.8.3 and
>   conversion to 0.8.4; their content is unchanged.
> - §4 (owner, 2026-11-04): README files for the PRD folders are inserted as 0.8.3
>   (`2026-11-04-prd-toolkit-0.8.3-prd-readmes-design.md`). Best practices move to 0.8.4 and
>   conversion to 0.8.5; their content is unchanged.
> - §4 (owner, 2026-11-06): the fixes from the 0.8.2 proof are inserted as 0.8.3
>   (`2026-11-06-prd-toolkit-0.8.3-backlog-design.md`). The READMEs move to 0.8.4 (their spec renamed
>   `2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md`), best practices to 0.8.5 and conversion to
>   0.8.6; their content is unchanged.

## 1. Why

Until 0.7 a PRD describes a service: OpenAPI operations, SQL tables, events, a test harness that
calls code. The owner's backlog (2026-11-01) asks for four things the toolkit cannot do:

1. **Skills and plugins.** A PRD can need a skill or plugin that the toolkit finds, installs or
   writes, recorded in §6; and the toolkit is extensible by users and other plugins (a wrapper
   such as an organization's own PRD plugin adds its platform's harness and contract types).
2. **Any output language.** Any programming language or platform, including targets that are not
   code at all ("a PRD for a tool to write end-user documentation for my widget"), and any human
   language, both for the PRD itself and for what is built from it.
3. **Conversion.** Take a project that has a PRD to another platform or language ("convert my
   dashboard project to another BI tool").
4. **Best practices.** Follow a platform's or language's best practices, from external sources
   Claude finds (with the user's approval) or the user adds.

They share one foundation, so they ship as one release line in three sub-releases.

## 2. The shared idea: target profiles and packs

A **target profile** says what an area of a PRD produces: a **pack**, and an **output language**.
`prd.md` §1 names the PRD's default profile; a `Target:` line in `features/<area>.md` overrides it
for one area, so one PRD can hold a service and its user guide, and a conversion can move one area
at a time.

A **pack** is a `pack.yaml` manifest plus files that make one kind of output authorable and
testable: contract types and their validators, extra test `target:` kinds, Levels and Harness slot
defaults, proposed §5 standards and §6 skills rows, the platform's vocabulary, rubric conventions
for model-judged test cases, and optionally a grader command. Packs ship in any plugin under
`prd-packs/<name>/`, or built into the toolkit. `prd_hooks.py install` vendors the packs a PRD names
into `.prd-toolkit/packs/`, and the gates always run the vendored, version-locked copy.

Two test kinds serve targets a script cannot check exactly: **script checks** where the output allows
them, and a **judged** case, where a model grader scores the output against the case's rubric and the
case passes at or above its threshold. The judged case is also how a PRD states black-box
requirements for model behaviour, which the toolkit's own PRD needs for its skills.

## 3. Invariants

Every sub-release keeps these:

1. **No pack means 0.7.** A PRD that names no pack uses the built-in `service` pack and behaves
   exactly as in 0.7. No existing PRD needs a migration.
2. **IDs survive.** Requirement, AC and T-ids never change because of a pack, a platform or a
   language. A conversion replaces contracts and the Harness, never IDs.
3. **The grammar is English.** Field labels, IDs and kinds stay English, as code keywords do. Prose,
   ACs, the glossary, acceptance `steps:` and published summaries follow the PRD's `language:`, and
   the EARS openers and vague words come from that language's table.
4. **Platform words warn.** A platform word in a requirement (from its pack's vocabulary) is a
   `warn` finding, never an error, so a PRD that never converts loses nothing.
5. **The toolkit stays generic.** It ships only platform-neutral packs (`service`, `document`).
   Platform packs live in wrapper plugins, never in prd-toolkit.
6. **The gates run the last released toolkit.** Lint, trace and the gates use the vendored copy of
   the toolkit and its packs, never a working tree.

## 4. Sub-releases

| Release | Delivers | Needs |
|---|---|---|
| **0.8.0** | Target profiles and packs (manifest, discovery, vendoring, lock); built-in `service` and `document` packs; `language:` with EARS and vague-word tables for `en` and `es`; output language; the `judged` case and `prd_judge.py`; lint severity `warn` and the `platform-word` rule | — |
| **0.8.1** | The machine interface: `--json` on lint, trace and context (status has it); `prd_change.py` (`ids`, `bump`, `record`, `approve`), the change bookkeeping moved out of skill text; `prd_gates.py` (`list`, `answer`) over every pending human decision; a review mode of `changing-prds` that edits nothing and prints one JSON verdict; `interface: 1` in every JSON document | 0.8.0 |
| **0.8.2** | The decision inbox: `prd_gates.py serve` and `wait`, one local page that lists every pending gate of a PRD across its worktrees and answers each through `answer_gate()`, with the 0.7.1 adoption panel as one of its cards | 0.8.1 |
| **0.8.3** | Fixes from the 0.8.2 proof, no feature: `prd_hooks.py vendor` and an exact refresh of `.prd-toolkit/` that `prd_build_check.py --diff` accepts in the toolkit's own repository; the standby promise checked against the vendored version; `prd_change.py record` writing a live block's Since and a contract item's IDs; seven `prd_build_check.py` fixes; eight inbox and gate fixes | 0.8.2 |
| **0.8.4** | README files for the PRD folders (a managed block in `docs/prd/README.md` and `docs/prd/<slug>/README.md`, written by `prd_block.py`, skipped by lint, the digest and the tester, and checked by `prd_hooks.py check --ci`) and an Overview tab on the published page, both from one set of facts, with §2's optional `Principles:` and `Getting started:` parts | 0.8.1, 0.8.3 |
| **0.8.5** | Best-practice sources: found by Claude and approved by the user, or added by the user; recorded per pack or per PRD; turned into §5 rows or checklist items. Finding, installing or writing a skill or a pack when a PRD needs one, recorded in §6 | 0.8.0 |
| **0.8.6** | Conversion: retarget an area or a whole PRD to another pack, with the `platform-word` findings as the worklist, contracts and Harness rebuilt, T-ids kept, and the old platform running until the new one is `verified` | 0.8.0, 0.8.5 |

Spec for 0.8.0: `2026-11-03-prd-toolkit-0.8.0-design.md`. Spec for 0.8.1:
`2026-11-03-prd-toolkit-0.8.1-design.md`. Spec for 0.8.2:
`2026-11-04-prd-toolkit-0.8.2-decision-inbox-design.md`. Spec for 0.8.3:
`2026-11-06-prd-toolkit-0.8.3-backlog-design.md`. Spec for 0.8.4:
`2026-11-04-prd-toolkit-0.8.4-prd-readmes-design.md`. The 0.8.5 and 0.8.6 specs are written when
their turn comes, each through its own brainstorm.

## 5. Related work

- **The toolkit's own PRD** (branch `feat/prd-toolkit-prd`) states its skills area with judged
  cases once 0.8.0 lands; that area waits for 0.8.0. Its lint-rules and scripts areas do not.
- **Wrapper packs.** An organization's wrapper plugin writes its platform packs against the 0.8.0
  manifest; the toolkit does not wait for one.
- **Timing.** The specs are written on `feat/prd-toolkit-0.8`. The 0.8.0 build branches from `main`
  after 0.7.1 (the adoption confirmation form) merges, since both touch `adopting-prds`.
