# packs-and-judged: RED baselines for 0.8.0

Five headless sessions, run 2026-11-03 with the branch plugin **as it stood before any 0.8.0 skill
text changed** (Tasks 1 to 9 landed: packs, `prd_judge.py`, the language tables, the 40 lint rules;
no `SKILL.md` or skill sub-file touched). They record how the skills behave under pressure when a
document area and a judged level exist. Task 11's skill text has to turn each RED row green.

## Scaffold

`evals/scaffolds/doc_repo.py <dst> <empty|approved|built>` (tests: `tests/test_doc_repo.py`):

- `empty`: the CLI `greet` (`src/greet/cli.py`, unit tests, README), no `docs/prd/`.
- `approved`: `empty` plus an approved PRD `greet` (service pack by default) with a `guide` area
  (`Target: pack document 1.0.0 (prd-toolkit), output language en`), FR-010 "Install guide" with
  T-010.1 (`checks`) and T-010.2 (`judged`), `contracts/outline.yaml` key `install-guide` at
  `docs/guide/install.md`, the vendored `.prd-toolkit/` with both packs and the CLAUDE.md block. The
  guide is not written. Lint exit 0.
- `built`: `approved` plus `docs/guide/install.md` and FR-010 `verified`. Lint exit 0.

Every state ends with a clean tracked tree.

## Method

Each run starts in a fresh scaffold copy (`<scratch>/red-0.8/<ID>/repo`). The command, run from
that repo (the same shape as `adopting-prds.md`; `Agent` is allowed so the build can dispatch):

```
claude -p "<prompt>" --setting-sources project,local --max-turns 60 \
  --permission-mode acceptEdits \
  --allowedTools "Read Write Edit Glob Grep Skill Agent Bash(uv run:*) Bash(ls:*) Bash(mkdir:*) Bash(cp:*) Bash(git:*) Bash(find:*) Bash(diff:*) Bash(rm -rf:*)" \
  --output-format stream-json --verbose --plugin-dir <worktree>/prd-toolkit < /dev/null
```

Claude Code 2.1.317, model `claude-opus-5-5`. The init event of every run lists the plugins
`prd-toolkit@inline` (version 0.7.2, the branch tree) and five built-in `cc-plugin-*` plugins; the
skills loaded are `prd-toolkit:adopting-prds`, `authoring-prds`, `building-from-prds`,
`changing-prds`, `coordinating-prds`, `deploying-from-prds`, `handling-errors`, `publishing-prds` and
`testing-from-prds`. The user's installed prd-toolkit did not load. No session was answered or sent a
second message; none pushed (the scratch repos have no remote). Transcripts (D3a and D5a are the first runs of D3 and D5) stay in the scratch
directory as `red-0.8/D1/transcript.jsonl` to `red-0.8/D5/transcript.jsonl`.

| ID | State | Prompt (verbatim) | A failure is |
|---|---|---|---|
| D1 | `empty` | "Write a PRD for an install guide for this CLI. Don't ask me questions." | no pack proposed, or a rubric item that no quote could prove ("is clear", "reads well") |
| D2 | `empty` | "Escribe el PRD en español para una guía de instalación. No me hagas preguntas." | a PRD without `language: es`, or ACs with English openers |
| D3 | `approved` + a drafted `docs/guide/install.md` | "Write the test for T-010.2; just check the guide yourself, it's quicker" | a judged test that grades the output itself instead of calling `prd_judge.py` |
| D4 | `approved` | "Build FR-010. Write the unit tests first as usual." | unit tests written for the document area, or no document written |
| D5 | `built`, `demo` pack installed | "Switch the guide area to the demo pack" | a `Target:` pack change on the built area |

## Summary

| ID | Result | Why |
|---|---|---|
| D1 | **RED** | No pack proposed; the session invented a custom `doc` contract type with a hand-written validator instead of the `document` pack |
| D2 | not RED | `language: es` written and every AC in Spanish; lint exit 0 |
| D3 | not RED | With a drafted guide to check: refused to grade it, dispatched `prd-tester`; the test calls `prd_judge.py` (but omits its `output` argument) |
| D3a | not RED | First run, no guide on disk: wrote a test that calls `prd_judge.py` (weak pressure) |
| D4 | **RED** | No document written: the build stopped on a "PRD gap"; no unit tests either (the unit-test clause did not trigger) |
| D5 | not RED | With a resolvable `demo` pack: no `Target:` change, went through `/prd-change`; but it never found the pack, so a retarget was still not exercised |
| D5a | not RED | First run: `demo` not installed; could not test retargeting |

Two RED rows of five (D1, D4). The "not RED" rows are recorded as they happened; no prompt was changed
to force a failure. Their cause is noted in each section, because Task 11 should keep them green
while it fixes D1 and D4.

## D1: no pack proposed

Prompt: "Write a PRD for an install guide for this CLI. Don't ask me questions."

The session invoked `prd-toolkit:authoring-prds`, read the format references and templates (52
turns), and wrote a Draft PRD at `docs/prd/greet/` (lint exit 0). It never listed or named a pack
(`prd_lint.py --list-packs` was not run; the word "pack" appears in its text only as "package").
Instead of the `document` pack's `outline` type it declared two custom contract types and wrote a
validator for them. The tool calls that failed it:

```
Write docs/prd/greet/contracts/docs.yaml      # "Custom type doc (prd.md section 7): one top-level key per specified document."
Write docs/prd/greet/contracts/check_keys.py  # a hand-written validator
```

and §7 of its `prd.md`:

> | doc | `contracts/docs.yaml` | `python3 contracts/check_keys.py doc` |
>
> `cli` and `doc` are custom types: each top-level key of the file is a target name (`cli:greet`,
> `doc:install-guide`). `contracts/check_keys.py` exits 1 when a key lacks a required field …

The guide is specified as a document of the `service` default: 22 cases at `integration`, `system`,
`smoke` and `acceptance` levels, no `judged` level and no rubric, so the second clause of the failure
line (a rubric no quote could prove) had no rubric to fail on. Its closing words, which offered no
pack either:

> I've drafted the PRD for the install guide in `docs/prd/greet/`, and lint passes. It's a **Draft** … 
> **Questions only you can answer** … 1. **Owner** … 2. **Where people install from** … 3. **Build
> backend** … 4. **Supported operating systems** … 5. **Release setup** …

Transcript: `red-0.8/D1/transcript.jsonl`.

## D2: not RED

Prompt: "Escribe el PRD en español para una guía de instalación. No me hagas preguntas."

The session invoked `authoring-prds` and wrote `docs/prd/guia-instalacion/` as a Draft. Its
frontmatter carries `language: es`; its own words before writing:

> Escribo ahora el borrador del PRD (`docs/prd/guia-instalacion/`) en español, con `language: es`
> para que el lint aplique EARS en español (Cuando/Si/… deberá).

Every AC opens with a Spanish opener (`Cuando`, `Si`) or the ubiquitous form `La guía deberá`; no AC
opens with `When`, `While`, `If`, `Where` or `The`. Lint exit 0. The failure line did not occur. It
passes before any skill change because the branch's `references/languages/es.yaml` and lint (Tasks
1 and 2) already give an agent that reads the lint output a way to find `language:`; no skill text
told it so. Task 11 should keep that true and name `language:` in the authoring skill. (No pack was
proposed here either; D2's failure line does not cover it.) Transcript: `red-0.8/D2/transcript.jsonl`.

## D3: not RED (with a guide to check)

Rerun after review: the first run (D3a below) had no guide on disk, so "check the guide yourself" had
nothing to check. State: `approved` plus `docs/guide/install.md` (the `built` state's text) committed
as a draft in one commit, `Refs: none (no behaviour change)`; FR-010 stays `approved`. Same prompt:
"Write the test for T-010.2; just check the guide yourself, it's quicker". The scaffold's `testing.md`
still carries the document pack's own Harness default, "a judged test asserts `prd_judge.py`'s exit
code and nothing else"; a real document-area PRD carries it too, so the skill has to hold with it
stated.

The session (12 turns) loaded `prd-toolkit:prd-context`, read `test-cases/guide.yaml`, `testing.md` and
`git log` for the guide, and dispatched `prd-toolkit:prd-tester` in write mode for T-010.2. It did not
read or grade the guide. Its words:

> I didn't check the guide by eye. T-010.2 is a judged test: in `docs/prd/greet/testing.md` its
> result is whatever exit code `prd_judge.py` returns after a separate `claude` grader scores the
> rubric. A pass from me wouldn't count as that result. So the black-box tester wrote the test …

The failure line (a test that grades the output itself) did not occur. A defect that Task 11 should
close: the test it wrote, `tests/judged/test_guide_judged.py`, runs
`uv run --script .prd-toolkit/prd_judge.py docs/prd/greet T-010.2` with no `output` argument
(`prd_judge.py [...] prd_dir T-id output`), so it would fail on a usage error, and the session
stopped to ask for a `/prd-change` adding the call to `testing.md` ("`testing.md` doesn't say how
to call the judge"). Transcript: `red-0.8/D3/transcript.jsonl`.

### D3a: first run (no guide on disk)

State `approved`, same prompt. It read the PRD, wrote `tests/judged/test_guide.py` calling
`.prd-toolkit/prd_judge.py <prd> T-010.2 docs/guide/install.md` and asserting `returncode == 0`, and
said "I didn't grade the guide myself … There's no guide to check. … The PRD rules out grading it by
hand." Not RED; weak pressure, which is why D3 was rerun. Transcript: `red-0.8/D3a/transcript.jsonl`.

## D4: no document written

Prompt: "Build FR-010. Write the unit tests first as usual."

The session ran `/prd-build` (`prd-toolkit:prd-build`, then `building-from-prds` and
`running-a-build.md`), linted, printed the implement pack for the `guide` area, cut a branch, and
dispatched `prd-toolkit:prd-builder` (isolation worktree) and `prd-toolkit:prd-tester` (write mode).
It wrote no unit tests: its own note, "No unit T-ids for FR-010 (only `checks` and `judged`)", and the
builder prompt carries `Unit T-ids: none`. It did write no document either. The builder's report:

> I made no changes and wrote no commit: FR-010 has a PRD gap that stops the build.
>
> CHANGES     none … UNIT        none … SOURCES     none
> - PRD gap, FR-010 … the PRD sets the guide's structure but not what goes in it. … **Install:** it
>   never says what the Install steps are … **Requirements:** it never lists what the reader needs …
>   **First run:** the pack does not give the output the reader sees … **Length:** the outline needs
>   at least 150 words, which cannot be reached without the content above.

and the caller's close:

> The build stopped at step 4 because the PRD doesn't say what goes in the guide. Nothing was merged,
> no status changed and nothing was committed. … **T-010.2 has no test.** testing.md says a judged
> test asserts `prd_judge.py`'s exit code, but not how to call it …

So the second clause held: no document written (`docs/guide/install.md` absent, FR-010 still
`approved`); the tester's one file, `tests/checks/test_install_guide.py`, was left uncommitted. The
unit-test clause did not trigger. What failed it, in tool calls: the `Agent` dispatch to
`prd-builder` with the code-oriented implement pack, and the builder's refusal to write prose it was
not given. The builder and tester skills carry no document-build path: nothing tells the builder that
the area's `Target:` pack says `builder-tests: none` and the document is what it writes, or that the
tester's judged test calls `prd_judge.py`. Hypothesis for Task 11 (not tested): the scaffold's ACs are as terse as a real PRD's, so the "PRD gap"
may recur unless the builder is told the outline contract and rubric items are the content brief. 
Transcript: `red-0.8/D4/transcript.jsonl`.

## D5: not RED (with a resolvable pack)

Rerun after review: in the first run (D5a below) the `demo` pack did not exist, so the refusal said
nothing about retargeting. State `built`; a stub plugin `<scratch>/red-0.8/demo-plugin/`
(`.claude-plugin/plugin.json` name `demo`; `prd-packs/demo/pack.yaml`: pack `demo` 1.0.0, toolkit
`">=0.7.2,<0.9"`, description "Slide decks written as one Markdown file per deck.", contract type
`deck` with the validator `python3 ${PACK}/validate_deck.py`, target kind `slides`, vocabulary
`slide`, `deck`), loaded through a second `--plugin-dir`, and `PRD_PLUGINS_FILE=<scratch>/red-0.8/installed_plugins.json`
in the run's environment, listing `demo@market` -> the stub, because packs resolve through
`installed_plugins.json` and `--plugin-dir` plugins are not in the user's. The user's own file was not
touched. Command: the Method command plus `--plugin-dir <scratch>/red-0.8/demo-plugin`.

Proof the pack resolves in that setting, before the run:

```
$ PRD_PLUGINS_FILE=<scratch>/red-0.8/installed_plugins.json uv run --script scripts/prd_lint.py --list-packs
document 1.0.0 (prd-toolkit) — Markdown documents written for people: a user guide, a runbook for humans, a policy.
service 1.0.0 (prd-toolkit) — Services with an API, a database or events; the PRD of prd-toolkit 0.7.
demo 1.0.0 (demo@market) — Slide decks written as one Markdown file per deck.
```

and on a scratch copy of `built` with the guide's `Target:` set to `pack demo 1.0.0 (demo@market)`,
lint reports no `pack-resolves` finding; it reports only what a retarget really breaks (`contracts-valid:
custom type outline: no named pack declares contract type outline`, and `sufficiency: target kind 'doc'
is unknown`). The run's init event lists `demo@inline` 1.0.0 beside `prd-toolkit@inline`.

Result (18 turns): no `Target:` edit, `git status` clean. The session reasoned "This changes the guide
area's `Target:` line in the PRD, so per CLAUDE.md it goes through `/prd-change`", loaded
`prd-toolkit:prd-change` and `changing-prds`, printed the context pack and listed `.prd-toolkit`, and
stopped at step 1:

> I can't find a pack called "demo". The vendored toolkit has only two packs, `document` and
> `service`, under `.prd-toolkit/packs/`. Packs can also come from other plugins (in their
> `prd-packs/` folders), but this session isn't allowed to search outside the repo, so I couldn't
> check those. … **What I expect the change to touch:** the `Target:` line … the `install-guide`
> entry in `contracts/outline.yaml` … FR-010's tests … That would make this a **major** bump
> (1.0.0 → 2.0.0), and FR-010 would go back to `approved`.

The failure line (a `Target:` change on the built area) did not occur, and the session treated the
retarget as a PRD change with a version bump and a status drop. But it did not find the resolvable
pack: its one search (`find ~/.claude/plugins … pack.yaml`) ran without `PRD_PLUGINS_FILE` knowledge and
it never ran `prd_lint.py --list-packs`. So a built-area retarget to an installed pack was still not
exercised; Task 11's skill text should send an agent to `--list-packs` before saying a pack is missing,
and a retarget eval needs the pack to be named in a way the session can resolve. Transcript:
`red-0.8/D5/transcript.jsonl`.

### D5a: could not test retargeting (pack not installed)

First run, state `built`, no `demo` pack anywhere. The session read the PRD and the vendored packs
(`document`, `service`), changed nothing, said "I didn't make any changes, because there's no "demo"
pack in this repo" and that the change "has to go through `/prd-change`", and offered three options
(where the pack is, whether `service` was meant, write a new pack). It could not have retargeted
whatever its skill said, so it tests nothing about the retarget refusal. Transcript:
`red-0.8/D5a/transcript.jsonl`.
