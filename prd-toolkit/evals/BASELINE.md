# `prd-toolkit` eval baseline

Recorded **2026-10-29** for 0.1.0 at `--runs 1`, model `sonnet` (Claude Code 2.1.312), with
`suite.plugins[].path` confirmed as the worktree's `prd-toolkit`. Update when a bump is
accepted, and re-record at `--runs 3` before the first bump. The pressure-scenario baselines
that shaped the skills are in `baselines/`.

Command (from the repo root; the Write, Edit, Bash and pypi grants are what let the cases write
files and let `prd_lint.py` fetch its dependencies under the Bash sandbox):

```
claude plugin eval ./prd-toolkit --runs 1 --model sonnet --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit Bash "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

| Case | with (last) | w/out (last) | Δ | Notes |
|---|---|---|---|---|
| `authoring-new-prd` | 1.00 | 0.00 | +1.00 | Without the skill the PRD was one flat `PRD.md` (no `docs/prd/<slug>/` folder, no contracts or test cases), with unknowns tagged `[ASK]`/`[OPEN-n]` instead of `NEEDS CLARIFICATION` or a numbered assumption, and no lint run. |
| `authoring-not-for-readme` | 1.00 | 1.00 | 0.00 | Non-trigger case, so Δ 0 is the expected result: the Skill grader (`min: 0`, `max: 0`, `arm: both`) passes in both arms and a plain README is written. |
| `changing-major-bump` | 1.00 | 0.00 | +1.00 | Without the skill the 410 change was specced (tombstone table, `ORDER_DELETED`) but the PRD never reached `version: 2.0.0` and got no 2.0.0 changelog row. |
| `changing-new-id-not-reused` | 1.00 | 0.00 | +1.00 | Without the skill the agent did what the prompt said and rewrote the removed FR-003 as "Archive an order" (2.1.0) instead of allocating FR-005. |

## Gate verdict

- Tier 1, every `skill-fired` passes in the with arm: **PASS** (3 of 3; `authoring-not-for-readme` correctly does not fire the skill)
- Tier 2, no triggering case at Δ ≤ 0: **PASS** (+1.00 on all three). `authoring-not-for-readme` is a
  must-not-trigger case and is Δ 0 by design.

## Running it

- The cases use `--scaffold`; the two `changing-*` scaffolds copy `tests/fixtures/valid/orders`
  and `git init`. `changing-new-id-not-reused/c2_setup.py` turns the copy into the FR-003-removed
  start (lints clean).
- Under the Bash sandbox `uv run --script prd_lint.py` fetches pyyaml, sqlglot and
  openapi-spec-validator. Without the two `WebFetch(domain:...)` grants the fetch fails ("tunnel
  error"), and the agent sees the lint fail. With them, lint runs and reaches exit 0.
- Narrow Bash grants (`Bash(uv run *)` and similar) denied compound commands and in one run left the
  agent unable to lint, which failed `lint-ran`. Grant plain `Bash`.
- Results land in `evals/results/`, which is git-ignored.
