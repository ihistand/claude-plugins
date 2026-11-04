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

## GREEN (Task 11)

The same five runs, rerun 2026-11-03 with the branch plugin **after** the 0.8.0 skill text (authoring
phases 1 to 3 and 6 with **Applying the pack**, adopting's area pack, the tester's **A judged case**,
the builder's `builder-tests: none` section, running-a-build's document-area dispatch, changing-prds'
**Packs and retargeting**, handling-errors' `prd_judge.py` exit 2). Same command, same prompts verbatim,
same scaffold states, `<scratch>/green-0.8/<ID>/repo`; D5 with the stub `demo` plugin as a second
`--plugin-dir` and `PRD_PLUGINS_FILE`, as in its RED rerun. Claude Code 2.1.317, model `claude-opus-5-5`;
the init event lists `prd-toolkit@inline` (and `demo` for D5). Runs one at a time, none answered.

| ID | Rounds | Result | Evidence |
|---|---|---|---|
| D1 | 1 | **GREEN** | ran `--list-packs`; the guide is a `document` area (`Target: pack document 1.0.0 (prd-toolkit), output language en`) with `contracts/outline.yaml` and §7 `\| outline \| `contracts/outline.yaml` \| pack \|`; no custom type, no `.py` in `contracts/`; 5 judged cases, every rubric item an observable claim; `- Profile: [ASSUMPTION A-01: …]` indexed `open`; lint exit 0 |
| D2 | 1 | GREEN (stays) | `language: es`, `- Pack: document 1.0.0 (prd-toolkit)`, every AC opens `Cuando`, `Si` or `La … deberá`; lint exit 0 |
| D3 | 1 | GREEN (stays), defect closed | dispatched `prd-tester`; `tests/judged/test_guide_judged.py` calls `prd_judge.py docs/prd/greet T-010.2 docs/guide/install.md` and asserts `returncode == 0`; the guide was never read; no stop for a `/prd-change` |
| D4 | 2 | **GREEN** in round 2 | round 1 still RED, for a scaffold defect (below); round 2: the builder wrote `docs/guide/install.md` from the outline (four sections in order, terms, word count checked) and committed it with `Refs: FR-010`; no unit test; no PRD or tester edit |
| D5 | 2 | GREEN (stays), defects closed in round 2 | round 1: the skill did not fire; round 2: `changing-prds` fired, ran `--list-packs`, found `demo 1.0.0 (demo@market)`, and refused with the exact line; no edit, no bump, no plan to drop a status |

### D1: GREEN

Phase 1 ran `uv run --script <worktree>/prd-toolkit/scripts/prd_lint.py --list-packs; echo "prd-lint-exit=$?"`,
then read the `document` pack's `pack.yaml`, `rubrics.md` and `clarify.md`, and wrote `docs/prd/greet/` with
the default `service` pack and the guide as its own area under `document`. Its §1:

> - Profile: [ASSUMPTION A-01: the PRD uses the default `service` pack and the area `guide` uses pack
>   document 1.0.0 (prd-toolkit); language en, output language en; basis: the request is an install guide
>   for a CLI, the request is written in English]

A rubric item, from `test-cases/guide.yaml`: "Each numbered step in the Install section names one action
the reader performs". No item holds "is clear", "reads well" or another judgement word. Transcript:
`green-0.8/D1/transcript.jsonl`.

### D2: stays GREEN

`docs/prd/greet/` with `language: es`, `- Pack: document 1.0.0 (prd-toolkit)` and a `- Profile:` assumption;
ten ACs, none with an English opener; lint exit 0. One note from its close: "El lint solo acepta unidades en
inglés ("palabras" no le vale)": `nfr-bound`'s units are English only, so its word-count bounds became FRs.
Transcript: `green-0.8/D2/transcript.jsonl`.

### D3: stays GREEN, the `output` argument now given

The session read the test case, loaded `testing-from-prds`, followed `dispatching.md` and dispatched
`prd-tester` in write mode. The tester wrote:

```python
def test_install_guide_judged():
    """@prd T-010.2"""
    r = subprocess.run(
        ["uv", "run", "--script", ".prd-toolkit/prd_judge.py",
         "docs/prd/greet", "T-010.2", "docs/guide/install.md"],
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0
```

and its close: "I wrote the T-010.2 test, but I didn't check the guide myself. … My own reading would be the
verdict of whoever wrote the test, which doesn't count." Transcript: `green-0.8/D3/transcript.jsonl`.

### D4: GREEN in round 2

**Round 1** (scaffold as Task 10 built it): the builder followed the new section: it read the pack's
manifest, the README and `pyproject.toml`, and ran the README's command to check it, which failed. Its
caller's close:

> The README says to run `uv run python -m greet World`, but in this checkout that fails with `No module
> named greet`. … Putting a workaround such as `PYTHONPATH` in the guide would make up a fact the PRD
> doesn't give.

That is the skill's rule 2 ("a fact neither the outline nor the repository holds" is a gap) applied to a
scaffold defect: the scaffold's README (and the `built` guide) gave a run command that does not run,
because the project has no build system and `src/` is on the path only for pytest. **Round 2 change:**
`evals/scaffolds/doc_repo.py` now writes `uv run --directory src python -m greet World` in the README and the
`built` guide, a command that runs; nothing else in the scaffold changed (`tests/test_doc_repo.py` passes).
No skill text changed for round 2. Transcript: `green-0.8/D4-r1/transcript.jsonl`.

**Round 2:** the caller dispatched the builder with `Unit T-ids: none` beside the tester's write. The builder
ran the First run command from the repository, wrote `docs/guide/install.md` (sections Requirements, Install,
First run, Common problems; the terms CLI and greeting; `wc -w` within the outline's length) and committed it
on its branch with `Refs: FR-010`, QUESTIONS none. The caller's words: "**Unit tests first:** FR-010 belongs
to the `guide` area, not `greet`, and that area uses the `document` pack (`builder-tests: none`). Neither of
its tests is a unit test". The build then stopped before the merge on two **tester** QUESTIONS the scaffold's
PRD does not answer ("what counts as a 'section' in the guide: a Markdown heading, at what level", and
whether other headings may sit between the four), as **Stops** says. So no status moved and the guide is on
the builder's branch, not merged. The failure line (unit tests written, or no document written) did not
occur. Transcript: `green-0.8/D4/transcript.jsonl`.

### D5: stays GREEN, the refusal now said

**Round 1:** no skill fired (no Skill call); the session searched `.prd-toolkit/`, `~/.claude/plugins` and
`packs.py` itself, said "There's no "demo" pack for the guide area to switch to", and offered a
`/prd-change`. No `Target:` edit, but both noted defects stayed. **Round 2 change:** the changing-prds
description gains "switching an area or the PRD to another pack or output language (its Target: or Pack:
line)" (pinned in `tests/test_packs_skills.py`). **Round 2:** "Switching an area's pack is a PRD change, so
I'll go through the change skill."; `changing-prds` fired; the context pack, then
`.prd-toolkit/prd_lint.py --list-packs` (which lists `demo 1.0.0 (demo@market)`); its close:

> I didn't make this change. The guide area is built, and the toolkit doesn't allow changing the pack of a
> built area:
>
> **retargeting an area is a conversion (prd-toolkit 0.8.3)**
>
> … So I've made no edits, version bump or plan to move FR-010 back to `approved`.

`git status` clean. Transcripts: `green-0.8/D5-r1/transcript.jsonl`, `green-0.8/D5/transcript.jsonl`.

### The scaffold after GREEN

Two changes to `evals/scaffolds/doc_repo.py`, both fixture defects found by these runs and the eval cases,
neither a change to what a state holds for the failure lines: the README's and the `built` guide's run command
(`uv run --directory src python -m greet World`, before D4's round 2), and, after the GREEN runs, a sentence in
the scaffold PRD's testing.md Assertions slot saying what a section of a document is (the tester's QUESTION
that stopped D4's round 2 before the merge, and two runs of `builder-document-no-unit`; `BASELINE.md`, 0.8.0).
D1 to D5 above ran before the second change. Every state still lints with exit 0 (`tests/test_doc_repo.py`).
