# prd-toolkit

A living PRD as the single authority agents build, test and deploy from: a PRD folder in the
repo with contracts and black-box test cases, a 27-rule linter and trace checks, a test agent
that cannot read your code, and skills to author, adopt and change it. Version 0.3.0.

Design: [docs/superpowers/specs/2026-10-29-prd-toolkit-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-design.md),
for 0.2 [docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md](../docs/superpowers/specs/2026-10-29-prd-toolkit-0.2-design.md),
and for 0.3 [docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md](../docs/superpowers/specs/2026-10-30-prd-toolkit-0.3-design.md).

## Install

```
/plugin marketplace add ihistand/claude-plugins
/plugin install prd-toolkit@ihistand
```

Restart Claude Code. To update an installed copy, run `claude plugin update prd-toolkit@ihistand`,
then `/reload-plugins` (or restart). The scripts run with `uv` (https://docs.astral.sh/uv/); each declares its own
dependencies (`pyyaml`, `sqlglot`, `openapi-spec-validator`) inline. A missing dependency prints an
install hint and exits 2.

## Commands and skills

| Command | Skill | Use |
|---|---|---|
| `/prd-new [slug]` | `prd-toolkit:authoring-prds` | Interview to a PRD folder `docs/prd/<slug>/`, lint it, dry-run it with prd-tester, approve it, install the CLAUDE.md block |
| `/prd-adopt [area]` | `prd-toolkit:adopting-prds` | Bring an existing repo under a PRD one area at a time, from the code, with the user's word on each requirement |
| `/prd-change <description>` | `prd-toolkit:changing-prds` | Change the PRD first, with new IDs and a version bump, before any code |
| `/prd-context [area] [IDs] [implement]` | `prd_context.py` | Print the focused context pack for one task: the decide pack, or with `implement` the implement pack |

## Lint CLI

```
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_lint.py" docs/prd/<slug>   # inside Claude Code
uv run --script prd-toolkit/scripts/prd_lint.py --list-rules
uv run --script prd-toolkit/scripts/prd_lint.py docs/prd/<slug> --sample-tids 3
```

- `${CLAUDE_PLUGIN_ROOT}` is set only inside Claude Code skills and commands. From a shell, use
  the plugin's install path (its `installPath` in `~/.claude/plugins/installed_plugins.json`)
  or a checkout of this repo, as the other two lines do.
- Output is one line per violation: `<file>:<line>: <rule>: <message>`.
- Exit 0 when clean, 1 on violations, 2 on usage, dependency or internal error.
- `--list-rules` prints the 27 rules. `--sample-tids N` prints up to N randomly chosen T-ids for the authoring
  dry run, one per line with the test-case file that holds it (`T-003.1 test-cases/nfr.yaml`), never a `level: unit` case; it exits 1 with `prd_lint: no non-unit T-ids to sample`
  when the PRD has none.

## Adopting an existing repo

`/prd-adopt [area]` runs the `adopting-prds` skill. It bootstraps `docs/prd/<slug>/` (first run
only), then takes one area at a time, an area being `features/<area>.md` plus
`test-cases/<area>.yaml`, bounded by the file globs in its Boundary cell. Progress is the adoption
map in `adoption.md`, and each area moves forward one state at a time:

`not started` → `extracted` → `confirmed` → `adopted`

- **extracted:** requirements are written as `as-built`, each with a `Source: <file>:<line> @<commit>`
  line. Apparent bugs become open `E-nnn` entries in `errors.md`, never requirements.
- **confirmed:** only on the user's word on each requirement and each `E-nnn`. Silence or "looks
  fine overall" confirms nothing, and with no answer the area stays `extracted`.
- **adopted:** only after a `prd-tester` suite where every T-id is `pass` or `known-failing E-nnn`,
  plus lint, the checklist, a dry run, `prd_trace.py` and the user's approval. Adoption changes no
  code. The first adopted area takes the PRD to `1.0.0`; each later area is a minor bump.

## Testing from the PRD

The `testing-from-prds` skill and the `prd-tester` agent write and run tests from the PRD folder
alone: it has never seen the code and must not look for it. A dry run writes tests for sampled
T-ids to a dry-run directory without running them; a suite writes tests to the test roots that
`testing.md` names and runs the harness commands. Every test carries an `@prd <T-id>` citation,
and the report lists QUESTIONS, TESTS, HARNESS CHOICES, FILES READ and, for a suite, RESULTS.
Dispatch it as a subagent (the Agent tool), not with `claude --agent`.

**Guard hook.** `hooks/hooks.json` registers `scripts/prd_tester_guard.py` as a PreToolUse hook
on Read, Glob, Grep, Write, Edit, NotebookEdit and Bash. It acts only when the hook's
`agent_type` is `prd-tester` (or ends with `:prd-tester`); every other session passes through.
For the tester it allows reads only of the PRD folder, the scratchpad and the test roots, writes
only to the scratchpad and the test roots (the PRD is read-only), and Bash only for the
`testing.md` harness commands (one simple command each) plus `ls`, `mkdir` and `uv run python -m py_compile`. It never fails open: with `testing.md`
missing or unparsable, only Read, Glob and Grep under the PRD folder are allowed.

**Limit.** The guard confines the tester's tool calls, not the processes the harness runs. A
`conftest.py` the tester writes can touch any file when pytest runs it. So callers run an
integrity check after each dispatch (a before and after snapshot of `git status`, the PRD folder's file list
and a tree of the working files), as in `skills/testing-from-prds/dispatching.md`. The hook runs
`python3`: under Python 3.7 or 3.8 it blocks the tester (and only the tester), but with no
`python3` on the PATH the hook exits 127, which Claude Code treats as non-blocking, so the guard
fails open.

## Trace CLI

`prd_trace.py` checks the PRD against the repo's tests and commits. It reads the test roots from
`testing.md` (falling back to `tests/`) for `@prd T-nnn.n` citations.

```
uv run --script "${CLAUDE_PLUGIN_ROOT}/scripts/prd_trace.py" docs/prd/<slug>
uv run --script prd-toolkit/scripts/prd_trace.py docs/prd/<slug> --range BASE..HEAD
```

| Rule | Finding |
|---|---|
| `t-implemented` | a T-id of a requirement that is not `removed` is cited by no test (in an adopted area, where the PRD has an adoption map) |
| `test-cites-live` | a test cites a T-id that does not exist in the PRD or belongs to a removed requirement |
| `commit-refs` | with `--range`, a commit touches a file inside an adopted Boundary and has no `Refs:` trailer (`Refs: none (no behaviour change)` counts) |
| `status-current` | a requirement is `verified` or `live` but a T-id has no citing test |

Where the PRD has an adoption map, `t-implemented` and `status-current` cover `adopted` areas
only. Output and exit codes match lint: `<file>:<line>: <rule>: <message>`; exit 0 clean, 1 on
findings, 2 on a usage, dependency or internal error. A malformed `--range` exits 2.

## Assumption status `awaiting <who>`

An assumption row in section 12 has status `open`, `confirmed`, `corrected` or `awaiting <who>`,
where `<who>` is a named person (`awaiting Sam Rivera`; a bare `awaiting` is a violation).
`awaiting <who>` is for intent only that person can confirm. Unlike `open`, it does not block
approval and may stay while the PRD is Approved. Adoption uses it for requirements whose intent
the user cannot state.

## Changelog

- **0.3.0:** `/prd-context` and `prd_context.py` (decide and implement packs); `adoption.md`; `Touches:` in `errors.md`; `changing-prds` works from the pack. Upgrading a 0.2 PRD: it fails `sections` until §8's table moves to `adoption.md` and §8 reads `See adoption.md.`, a patch bump. The managed `CLAUDE.md` block's wording changed in 0.3: re-render it with `prd_block.py`; until then, `prd_block.py --check` reports it stale.
- **0.2.0:** `/prd-adopt` and `adopting-prds`; `testing-from-prds`, the `prd-tester` agent and its guard hook; `prd_trace.py`; the `awaiting <who>` assumption status. Upgrading a 0.1 PRD: it fails `sections` until its `testing.md` Harness has every slot, in order, and a `Test roots:` list.
- **0.1.0:** `/prd-new`, `/prd-change`, `prd_lint.py` (27 rules) and `prd_block.py`.

## CLAUDE.md block

`prd_block.py` writes the managed block that points agents at the PRD. It is deterministic, not
written by an agent.

```
uv run --script prd-toolkit/scripts/prd_block.py docs/prd/<slug> [--claude-md PATH] [--check]
```

`--check` reports whether the block is current without writing.

## Folder layout

```
docs/prd/<project>/
├── prd.md                  index: metadata, goals, glossary, registries, ID registry, changelog
├── features/<area>.md      FR blocks with EARS acceptance criteria and T-ids
├── test-cases/<area>.yaml  one entry per T-id
├── contracts/              openapi.yaml, schema.sql, events.md, errors.yaml, permissions.yaml,
│                           config.yaml, data-classification.yaml, dependencies/, fixtures/
├── nfr.md                  NFRs with numeric bounds
├── testing.md              levels, harness, environments, sign-offs
├── operations.md           environments, deploy and rollback runbook
└── errors.md               the Error-Driven Development ledger
```

The exact syntax lint parses is `references/prd-format.md`. The starting files are in
`templates/prd/`.

## Tests and evals

```
uv run --directory prd-toolkit pytest -q
```

The plugin eval: run the command recorded in `evals/BASELINE.md` (0.2 baseline). The `--scaffold`
flag is required by the scaffolded cases, `Agent` lets the caller dispatch `prd-tester`, and the
pypi grants let `prd_lint.py` fetch its dependencies under the Bash sandbox:

```
claude plugin eval ./prd-toolkit --runs 3 --model sonnet --scaffold --trust-plugin --no-publish -j 4 --keep-temp \
  --json <out>.json --allow-tools Write Edit Bash Agent "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
```

## Credits

Adapted from GitHub Spec Kit, cc-sdd, BMAD-METHOD, mattpocock/skills and Anthropic's
doc-coauthoring skill. See [NOTICE](./NOTICE).
