# prd-toolkit 0.8.6: best-practice sources, and the next adopted area — backlog

> **Date:** 2026-11-08
> **Author:** Ivan Histand & Claude Code
> **Status:** Backlog, not designed. Each item becomes a section and plan tasks in 0.8.6's own
> brainstorm, or moves to a later release.
> **Extends:** `2026-11-08-prd-toolkit-0.8.5-design.md` and the specs it extends, under
> `2026-11-03-prd-toolkit-0.8-umbrella.md`.
> **Needs:** 0.8.5 merged.
>
> **Revisions.**
> - Created (owner, 2026-11-08): item 2 joins the umbrella's best-practice sources (item 1).

## 1. Backlog

1. **Best-practice sources.** As the umbrella's 0.8.6 row says: sources found by Claude and approved
   by the user, or added by the user; recorded per pack or per PRD; turned into §5 rows or checklist
   items; finding, installing or writing a skill or a pack when a PRD needs one, recorded in §6.
2. **Adopt `lint-structure` in the toolkit's own PRD.** The second adopted area, after `lint-cli`,
   through `/prd-adopt lint-structure`: extracted as built, confirmed by the owner in the form, and
   closed by a characterization suite. A minor version of the toolkit's PRD. Adoption changes no
   code; the bugs it finds are recorded and fixed later through `/prd-error`.
   - **Its Boundary first.** `adoption.md` gives it `prdlint/rules/structure.py`,
     `references/prd-format.md` and `templates/prd/**`. The format reference and the templates change
     in almost every release (0.8.5 edits `prd-format.md`), so adopting them as they stand puts each
     such edit behind a `/prd-change`. Weigh narrowing the Boundary to `structure.py` before
     extraction.
   - **The policy it starts** (owner, 2026-11-08): one area adopted per release, after the release
     that last reshaped it. The order agreed: `lint-structure`; then `lint-ids` and `lint-testcases`;
     then `change` and `build-check`; then `trace-and-hooks`, `context` and `status`; then `deploy`,
     `tester-guard`, `publish`, `gates` and `links`, once they stop changing every release; `skills`
     last, with judged cases. The PRD's goal (§2) is every area adopted before the plugin's 1.0.0.
