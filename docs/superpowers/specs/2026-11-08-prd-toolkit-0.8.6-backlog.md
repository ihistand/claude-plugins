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
> - Owner, 2026-11-09: items 3 (the rest of issue #24) and 4 (the changelog's PRD version), after
>   PR #26 merged.

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
3. **One uv environment per script path, per clone (the rest of issue #24).** uv keys a cached
   `uv run --script` environment on the script's path, not its contents. Each clone or worktree
   therefore adds one environment to `~/.cache/uv/environments-v2` for every prd script its git
   hooks and skills run, and nothing removes them. On 2026-11-09 the cache held 26,888 environments,
   about 89–99 GB of disk and about 27 million files; two new ones were created by another session's
   hooks while the cache was being deleted. PR #26 (NFR-019, E-008 resolved, PRD 6.1.0) fixed only
   test runs: a test session runs on its own uv cache (`prd-toolkit/.uv-test-cache/`, or
   `PRD_TEST_UV_CACHE`) and deletes that cache's environments at the end. The hook and skill case
   is this item.
   - **A likely fix:** run the scripts as `uv run --with <packages> python <script>`, which in a
     test on 2026-11-09 created no environment per script path, unlike `uv run --script`.
   - **The fix must keep the vendored copies working.** Generated CI, the git hooks and the skills
     run `uv run --script .prd-toolkit/<script>.py` today, in this repository and in every repository
     that installed the toolkit. Whatever form replaces it has to keep those working, or rewrite them
     through `prd_hooks.py install` / `vendor` and `ci`, with an upgrade note.
   - References: issue #24 and its comments; E-008 in `docs/prd/prd-toolkit/errors.md`.
4. **The changelog's PRD version.** The 0.8.5 changelog says "The toolkit's own PRD is at 6.0.0
   (approved b99cfac)". PR #26 moved the PRD to 6.1.0 (approved 7ed632f) after 0.8.5 shipped. The
   0.8.6 changelog names the PRD version it reaches: 6.1.0, or later if 0.8.6 changes it.
