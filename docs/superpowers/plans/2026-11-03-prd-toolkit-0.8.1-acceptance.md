# prd-toolkit 0.8.1 acceptance run

> **Date:** 2026-11-04 (UTC)
> **Plan:** Task 13 (Steps 1 to 4). **Spec:** `2026-11-03-prd-toolkit-0.8.1-design.md` §3 to §6, and for P1 the
> 0.8.0 spec §13 P1 pass line with its Revisions (the `document` pack fix).
> **Result:** **M1 passes (attempt 3, after F-1). M2 passes (attempt 1). P1 fails the dry-run clause.**
> - **M1, a client's change loop: pass.** It took three attempts.
>   - Attempt 1 failed on a harness defect: the runner narrowed `Bash`, so the review could not write its verdict.
>   - Attempt 2 failed because the review judged the driver's edit a meaning change, with `ready: false`.
>   - Attempt 3 found toolkit defect F-1 (`approve` refused when `.prd-review.json` is git-ignored). F-1 was fixed
>     and the attempt finished at step 7.
>   - The approval commit carries `Reply: "approved"`, the gate is gone, and the review edited nothing.
> - **M2, gates: pass.**
>   - On `error_repo.py failed-deploy`, `list --json` shows `error-class:E-001`. Its `answer` lands verbatim in
>     `errors.md`.
>   - On `deploy_repo.py at-gate`, `list --json` shows `deploy-step:<run>:3`. Its `answer` lands verbatim in the run
>     log, and `prd_deploy.py resume` runs steps 4 and 5 to `done`.
> - **P1, the Spanish guide rerun on the fixed `document` pack: fail on the dry-run clause.** It was one attempt, a
>   single session from `doc_repo.py empty`.
>   - Lint exits 0 with Spanish ACs.
>   - Five dry runs all failed, across 6 clarification rounds. One round was content; five came from dry runs, and
>     the sixth was left unanswered at the owner's cap.
>   - Dry run 4 sampled a judged T-id, and its test was correct. That run failed on its `checks` questions.
>   - `/prd-build` and the levels were not reached.
>   - The pack's parsing default reached the Harness, and round 1 asked no parsing question. But it does not settle
>     what text the checks compare (O-5).
>
> One toolkit defect, F-1, was found and fixed test-first (6edbb46, re-vendored in 7b2f7de). No scaffold defect was
> found. No F-n touches the lint-cli Boundary. Headless cost: **$51.99**.

**Scope.** Everything ran in scratch repositories under the session scratchpad (`<scratch>` =
`…/scratchpad/proof-0.8.1/`):
- `m1`, from `deploy_repo.py <scratch>/m1 ready`;
- `m2-error`, from `error_repo.py <scratch>/m2-error failed-deploy`;
- `m2-deploy`, from `deploy_repo.py <scratch>/m2-deploy at-gate`;
- `p1`, from `doc_repo.py <scratch>/p1 empty`.

No repository has a remote, and nothing was pushed. The only deploys went to m2-deploy's local `.deploy/`.

## Run setup

- **Sessions.**
  - Headless `claude -p` (Claude Code 2.1.318), `--model claude-opus-5-5`, `--max-turns 200`,
    `--permission-mode acceptEdits` and `--verbose`.
  - `--plugin-dir <worktree>/prd-toolkit`, with `--setting-sources project,local`, so the installed prd-toolkit
    stays disabled.
  - The default allow list is 0.8.0's: `Read Write Edit Glob Grep Skill Agent` plus `Bash(…)` for `uv run`, `ls`,
    `mkdir`, `cp`, `git`, `find`, `diff`, `rm -rf`, `wc`, `echo`, `mktemp`, `GIT_INDEX_FILE=*` and `sort`. This run
    adds `cat`, plus `--add-dir <the user temp directory>`.
  - Every init event shows `prd-toolkit@inline` 0.8.1. Commands use the `/prd-toolkit:<command>` form, which is
    how a `--plugin-dir` plugin names them.
- **The runner** is `<scratch>/run.sh`, 0.8.0's with these changes:
  - W is the 0.8.1 worktree, and P is `proof-0.8.1`.
  - `--model` is named explicitly.
  - `TOOLS` sets `--tools` to the names given, and keeps only those in the allow list, with Bash narrowed to the
    rules above.
  - `TOOLS_ALLOW=exact` allows the `TOOLS` names verbatim (`Bash` unrestricted). It was added after M1 attempt 1;
    see the harness defect there.
  - `OUTFMT` picks `json` or `stream-json`. With `--verbose`, `json` prints the whole message array, so the init
    event can still be checked.
- **The M1 review session** ran with `OUTFMT=json`, `TOOLS="Read Grep Glob Bash Agent"` and (from attempt 2)
  `TOOLS_ALLOW=exact`. That makes its init `tools` list exactly `Task, Bash, Glob, Grep, Read`. This is the
  spec's `claude -p "/prd-change --review <dir>" --output-format json` with the tools `Read`, `Grep`, `Glob`,
  `Bash`, `Agent`.
- **The client steps** (bump, record, lint, trace, gates list and answer, error propose, deploy resume) ran with no
  model, as `uv run --script <worktree>/prd-toolkit/scripts/<script>` from each scratch repo's root.
- **Heads** (the `--plugin-dir` tree):
  - 51a13b0 for M1's three reviews, the probes and P1a;
  - 7b2f7de (F-1's fix, re-vendored) for P1b to P1g, which changes only `approve`.
  - M1 attempt 3's second `answer` ran at 6edbb46.
- **Files.**
  - Each session's prompt, output, stderr, argv and meta are `<scratch>/runs/<id>.prompt.md`, `.jsonl`, `.stderr`,
    `.argv` and `.meta`.
  - M1's earlier attempts are under `runs/m1-att1/` and `runs/m1-att2/` (attempt 2's verdict is
    `runs/m1-att2/prd-review.json`).
  - State tarballs: `m1-before-review`, `m1-att3-before-review`, `p1-start`, and `p1-after-P1a` to `p1-after-P1g`.

## Replies sent

M1's reply, `approved`, is the client's `--reply` to `prd_gates.py answer` on the approval gate, whose question the session's verdict produced. That is the routine stop of "approving a PRD
change". The M2 replies were passed the same way, on two scaffold gates:
- **M1** (`approval:change/greet-output`, after the review showed its verdict): `approved` (standing scratch-reply
  authorization: approve a PRD change).
- **M2 error-class** (`error-class:E-001`): `Sí, "code bug" — the hardcoded "Hey" is the cause.` This is the Step 2
  scaffold gate's answer, chosen with quotes, an em dash and non-ASCII to check the verbatim path (Review Focus 2).
  The class is the one the driver proposed from the planted defect (b6e437e hardcodes `"Hey"`).
- **M2 deploy-step** (`deploy-step:20261104T203807Z-all:3`): `deploy production (staging printed "Hi, World!"; sí)`
  (standing authorization: a staging human step; the runbook's step asks for "deploy production").
- **P1** (session 4dba31b1-e6fe-4dcb-adb8-47688fea6f12). Each prompt is in `runs/P1<x>.prompt.md`:
  - P1b: `1A 2A 3A 4A 5A` (Ivan, verbatim: "1A 2A 3A 4A 5A, and yes to a forced dry run")
  - P1c: `Confirmo A-01 a A-11 y las dos filas.` (Ivan: "confirm all"; this wording, which I recommended, carries it)
  - P1d: `R2: 1A 2A 3A 4A` (Ivan, verbatim: "R2: 1A 2A 3A 4A.  Yes, use the commonmark structures")
  - P1e: `R3: 1A 2A 3B 4A 5A. 3B porque en CommonMark el texto plano de una imagen es su texto alternativo. Sigue
    CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.` (mine, under Ivan's parsing leave,
    quoted in P1 below)
  - P1f: `R4: 1A 2A 3A 4B. 4B porque CommonMark solo distingue espacio en blanco Unicode y puntuación Unicode; una
    marca combinante (M*) es parte de la palabra. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás,
    texto exacto.` (mine, under the same leave)
  - P1g: `R5: 1A 2A` (Ivan, verbatim: "R5: 1A 2A (1 more run)")
  - Round 6: not answered (Ivan's cap).

## M1: a client's change loop

Pass lines (plan Task 13 Step 1): the commit carries the reply; the gate is gone; `git diff --stat` shows the review
edited nothing.

### Attempt 1: harness defect

- Edit: AC-002.1 gained `, followed by `, <name>!``, on branch `change/greet-output`.
- `prd_change.py bump docs/prd/greet --base HEAD --json` gave:

  ```
  {"interface": 1, "kind": "change.bump", "level": "needs judgment", "items": [{"id": "AC-002.1", "file": "features/greet.md", "line": 14, "change": "changed", "level": "needs judgment", "reason": "an AC whose text changed (not equal after lowercasing, removing punctuation and collapsing whitespace)"}]}
  ```
- **Review** M1a (session 1236e817-25e9-4150-ad76-253271c7882b, 17 turns, $3.18):
  - It followed `reviewing-a-change.md` step by step: upstream (none, base `main`), `rev-parse`, `digest`, `bump`,
    `git diff`, `prd_context.py`, lint 0, no `links.md`, digest again. It decided AC-002.1 `patch`.
  - It could not write the verdict. Claude Code refused both heredocs the skill prescribes, `cat >
    docs/prd/greet/.prd-review.json <<'VERDICT'`, with `Contains brace with quote character (expansion
    obfuscation)`. A `python3` fallback was outside the allow list.
  - The session stopped and wrote nothing.
- **Probes** (one command each, in `<scratch>/probe`):
  - With the narrowed list, every heredoc whose body has a `{` and a `"` is refused: multi-line, one line, and
    without nesting (probe1 bac74e68…, $2.46).
  - An `echo -E '<json>'` with `'` for apostrophes fails with `Parse error` (probe2 d3fdc86c…, $2.21).
  - With `Bash` allowed unrestricted, as the spec's tool list reads, the same heredoc runs (probe3 e1437ef2…,
    $2.20).
- **Judgment: harness defect, not a toolkit defect.** The spec gives the review the tool `Bash`. The runner had
  narrowed it to prefix rules, and Claude Code's validator applies under prefix rules but not to an unrestricted
  allow. The fix was `TOOLS_ALLOW=exact`. See O-1 for what this means for clients.

### Attempt 2: the edit crossed a glossary term

- Same edit, same state (the review had written nothing). Review session 2dd23c9b-6135-4615-8135-5e62541b1418
  (14 turns, $3.00), with no permission denials. It wrote the verdict by heredoc.
- It decided AC-002.1 **major**, `ready: false`. Its reason: the glossary defines `greeting` as "The word before the
  comma", so the old AC asked for that word alone and the new one adds `, <name>!`.
- Its two blockers:
  - `incomplete change: AC-002.1 changed meaning (major) but its test case T-002.1 [system] was not revised …`;
  - `incomplete change: FR-002 still reads 'Status: verified (since 1.0.0)'; a changed requirement goes to
    'Status: approved'`.
- **Judgment: the driver's edit plus a model lapse, not a toolkit defect.**
  - Against this PRD's glossary, the edit was arguably a change of meaning, so `ready: false` is a defensible
    verdict, and the review edited nothing.
  - The lapse: the first blocker describes T-002.1 without the session having opened it, as it said itself. T-002.1
    already expects `Hi, World!`.
  - Attempt 1 had decided the same item `patch`: the judgment of a `needs judgment` item is not deterministic (O-2).
  - The gate never became pending, so steps 4 to 7 could not run.

### Attempt 3: pass, after F-1

- Reset: `git restore` of the edit, and attempt 2's verdict removed (kept as `runs/m1-att2/prd-review.json`).
- **Step 1**, a wording-only edit: AC-002.2 `When the launcher of an install is run with …, it shall print the PRD
  version the install was made from.` → `When an install's launcher is run with …, it shall print the PRD version
  that the install was made from.`
- **Step 2:** `bump --base HEAD --json` gave `"level": "needs judgment"`, one item `AC-002.2 features/greet.md:15`
  with the same reason.
- **Step 3**, review M1a (session 6dfdb8d4-0e35-48df-8718-4139fc07366c, 15 turns, $0.83). The verdict:

  ```json
  {"interface": 1, "kind": "review", "head": "63999660c7145c90f927600e68a4332929ed05ee", "digest": "73fe8711629dc1b129aedf12305e30964c24c560a63b4e8038f633774280d05a", "restate": "Reword AC-002.2 (\"the launcher of an install\" to \"an install's launcher\", \"the PRD version the install\" to \"the PRD version that the install\") without changing what the launcher prints for --prd-version.", "touches": ["FR-002", "AC-002.2", "T-002.1", "T-002.2"],
   "impact": {"exit": 0, "lines": []}, "bump": {"level": "patch", "decided": [{"id": "AC-002.2", "file": "features/greet.md", "line": 15, "level": "patch", "reason": "wording only: same trigger (the install's launcher run with --prd-version) and same response (print the PRD version the install was made from); no test that passes today can fail after it"}]},
   "dry_run": {"tids": [], "open": 0, "dismissed": 0, "record": "no dry run (wording only)"},
   "ready": true, "blockers": []}
  ```
- **The review edited nothing.**
  - After the session, `git diff --stat` printed ` docs/prd/greet/features/greet.md | 2 +-`, which is the
    driver's one-line edit.
  - `git status --short --untracked-files=all` printed only ` M docs/prd/greet/features/greet.md`.
  - The verdict file is ignored (`git check-ignore -v`: `.gitignore:6:.prd-review.json`).
- **Step 4:** `record docs/prd/greet --base HEAD --bump patch --change "AC-002.2 reworded, same behaviour"
  --json` gave:

  ```
  {"interface": 1, "kind": "change.record", "version": "1.0.1", "row": "| 1.0.1 | 2026-11-04 | AC-002.2 reworded, same behaviour; pending | FR-002, AC-002.2 |"}
  ```

  The digest before and after `record` was the same, `73fe8711…`.
- **Step 5:** `prd_lint.py --json` gave `{"interface": 1, "kind": "lint", "prd": "greet", "version": "1.0.1",
  "dir": "docs/prd/greet", "findings": [], "errors": 0, "warnings": 0}`, exit 0. `prd_trace.py --json` gave
  `{… "kind": "trace", … "errors": 0, "warnings": 0, "findings": []}`, exit 0.
- **Step 6:** `prd_gates.py list docs/prd/greet --json` gave:

  ```
  {"interface": 1, "kind": "gates", "prd": "greet", "gates": [{"id": "approval:change/greet-output", "kind": "approval", "title": "Approve greet 1.0.1", "question": "Reword AC-002.2 (…) without changing what the launcher prints for --prd-version. Approve it, or send it back with changes?", "evidence": ["no dry run (wording only)", "touches: FR-002, AC-002.2, T-002.1, T-002.2"], "choices": ["approve", "changes"], "source": ".prd-review.json"}]}
  ```
- **Step 7**, `prd_gates.py answer docs/prd/greet approval:change/greet-output --choice approve --question
  "<the listed question>" --reply "approved" --json`, at 51a13b0:

  ```
  {"interface": 1, "kind": "gates.answer", "gate": "approval:change/greet-output", "result": {"stdout": [], "exit": 1, "stderr": ["refused: git add failed: The following paths are ignored by one of your .gitignore files:", "docs/prd/greet/.prd-review.json", …]}}
  ```

  That is **F-1** (below). The refusal also left the index half-staged (`AD CLAUDE.md`, `MM
  docs/prd/greet/prd.md`). The work tree itself was rolled back.
- **After F-1's fix** (6edbb46):
  - Driver action: `git reset -q`, to undo the defect's staging. The tree then matched the state before the answer:
    two modified files, no `CLAUDE.md`, the §14 row `; pending`, the digest `73fe8711…`.
  - The gate was listed again with the same question.
  - The same `answer` gave `{"interface": 1, "kind": "gates.answer", "gate": "approval:change/greet-output",
    "result": {"stdout": ["approved greet 1.0.1 3562722"], "exit": 0}}`.
- **Pass checks:**
  - The commit, 3562722:

    ```
    docs(prd): approve greet 1.0.1

    Reply: "approved"
    Dry run: no dry run (wording only)

    Refs: none (no behaviour change)
    ```

    It holds `CLAUDE.md` (the block, +24), `features/greet.md` and `prd.md`. The scratch repo's commit-msg and
    pre-commit hooks passed.
  - **The gate is gone:** `list --json` gives `"gates": []`.
  - `.prd-review.json` is deleted, and `git status` is clean.
  - The PRD reads `version: 1.0.1`, `status: Approved`, and the §14 row reads `… AC-002.2 reworded, same behaviour;
    no dry run (wording only) | FR-002, AC-002.2 |`.
  - Lint 0, `prd_trace.py --range HEAD~1..HEAD` 0, and `prd_block.py --check` 0.

## M2: gates

Pass line (plan Task 13 Step 2): `list --json` shows `error-class` and `deploy-step`. Each `answer` lands in
`errors.md` and in the run log, and `prd_deploy.py resume` then goes on.

- **error-class**, on `m2-error` (E-001 `Classification: unclassified`, from the failed staging deploy):
  - `list --json` before a proposal gave `"gates": []`. An unclassified entry is not a gate.
  - `prd_error.py propose docs/prd/greet E-001 --class "code bug" --diagnosis "src/greet/cli.py:23 hardcodes the
    greeting \"Hey\" (b6e437e), …"` gave `E-001 proposed code bug`.
  - `list --json` gave `{"id": "error-class:E-001", "kind": "error-class", "title": "Staging deploy failed",
    "question": "Proposed class: code bug. Confirm it, or correct it to another class.", "evidence": [],
    "choices": ["confirm", "correct"], "source": "errors.md:3"}`.
  - `answer docs/prd/greet error-class:E-001 --choice confirm --question "<listed>" --reply 'Sí, "code bug" — the
    hardcoded "Hey" is the cause.' --json` gave `{… "result": {"stdout": ["E-001 confirmed code bug"], "exit":
    0}}`.
  - `errors.md` now reads `Classification: code bug` and `Confirmed: 2026-11-04, "Sí, "code bug" — the hardcoded
    "Hey" is the cause."`. That is the reply byte for byte.
  - `list` afterwards gave `"gates": []`, `prd_lint.py` exit 0, and `prd_error.py list --open` gave `E-001
    confirmed code bug - Staging deploy failed`.
- **deploy-step**, on `m2-deploy` (run 20261104T203807Z-all, stopped at step 3 `human`):
  - `list --json` gave `{"id": "deploy-step:20261104T203807Z-all:3", "kind": "deploy-step", "title": "Run
    20261104T203807Z-all step 3: Approve production", "question": "Approve production. read the staging results
    and reply \"deploy production\"", "evidence": ["Check: the reply says \"deploy production\""], "choices":
    ["confirm"], "source": "operations.md"}`.
  - `answer … --choice confirm --question "<listed>" --reply 'deploy production (staging printed "Hi, World!";
    sí)' --json` gave `{… "result": {"stdout": ["confirmed: step 3 run=20261104T203807Z-all"], "exit": 0}}`.
  - The log's last record: `{"kind": "confirm", "step": 3, "reply": "deploy production (staging printed \"Hi,
    World!\"; sí)", …}`. That is verbatim.
  - `list` afterwards gave `"gates": []`.
  - `prd_deploy.py resume docs/prd/greet --run 20261104T203807Z-all` printed `resume: 20261104T203807Z-all`,
    `step 4 agent production: pass`, `step 5 agent production: pass` and `prd-deploy: done step=5 …`, exit 0.
  - `.deploy/production/bin/greet World` prints `Hello, World!`.

## P1: the Spanish guide on the fixed `document` pack

Pass line (0.8.0 spec §13 P1, as written): lint exits 0 with Spanish ACs; the dry run passes with judged T-ids in its
sample; `/prd-build` writes the guide; the `checks` and `judged` levels pass, with `.prd-judge/` records showing
every median at or above its threshold.

- **Prompt.** P1a is 0.8.0's P1a, byte for byte through the facts list, plus a block "Decisiones que ya tomé para
  esta guía". That block restates the owner's own 0.8.0 answers about this guide's content: 1A (Requisitos names
  curl), 2A (Python out of scope), 3A (the word count), 5A (title and intro paragraph), A-02 (which sections hold
  numbered steps) and 4A (`markdown-it-py` in `dev`). It leaves out every parsing answer, because those are what the
  fixed pack must now settle.
- **P1a** (session 4dba31b1-e6fe-4dcb-adb8-47688fea6f12, 53 turns, $2.06):
  - It wrote the Draft `docs/prd/guia/` (untracked, nothing committed): 12 FR, 22 cases (19 `checks`, 3 `judged`)
    and assumptions A-01 to A-10. `prd-lint-exit=0`.
  - **The pack fix took effect.** `testing.md` Assertions reads "Una prueba de `checks` analiza el documento como
    CommonMark 0.31.2 después de normalizarlo a NFC [ASSUMPTION A-06: … el predeterminado del pack document; con
    `markdown-it-py` en su modo `commonmark`]. Una sección es un título de nivel 2 cuyo texto es igual a una entrada
    de `sections` del outline, cada entrada titula exactamente una sección …". The parsing standard was not asked as
    a question: the default stands as an assumption to confirm at approval.
  - It moved the 250 to 900 word bound to FR-012, because `nfr-bound` knows only English units. This is the
    carried item "Spanish units in `nfr-bound`".
  - **It stopped at clarification round 1** with Q-01 to Q-05, recorded in §13 as `[NEEDS CLARIFICATION]`. Each is a
    content decision about the guide, not an approval or a pack, language or profile confirmation, so none was
    answered:
    - **Q-01:** the steps say "abre una terminal", but Requisitos names only Python, uv and curl, so the rubric item
      "ningún paso usa una herramienta que Requisitos no nombre" fails. A (recommended): Requisitos also names the
      terminal; B: reword the rubric item; C: no change.
    - **Q-02:** how the reader reaches the repository root. A (recommended): a first step in Primera ejecución with
      `cd ruta/de/tu/copia/de/greet` and a sentence asking the reader to change the path; B: "abre la terminal en la
      carpeta del repositorio", without a command; C: something else.
    - **Q-03:** how `Hello, Mundo!` is shown. A (recommended): in its own code block right after the command's
      block, in the same step; B: as inline code in the step's text.
    - **Q-04:** the intro paragraph's "breve". A (recommended): at most 60 words, checked in `checks`, with its
      content judged in T-002.3 by two items ("dice qué consigue el lector al seguir la guía", "dice qué es uv"),
      threshold 1.0, 3 runs; B: another word count; C: the word limit only.
    - **Q-05:** the style (tuteo, instructional tone, plain language). A (recommended): a second judged case,
      T-011.1, threshold 0.75, 3 runs, with four items (each numbered step opens with a tú imperative; no sentence
      uses usted; each step says what the reader does; each technical term other than CLI, uv and terminal is
      explained where it first appears); B: the same items in T-010.1, 8 items, threshold 0.87; C: style as an
      outline guideline only, and FR-011 removed.
- **P1b**, the owner's answer, sent verbatim: `1A 2A 3A 4A 5A` (Ivan, 2026-11-04, answered at the stop; relayed by the
  coordinator as "1A 2A 3A 4A 5A, and yes to a forced dry run").
  - Session 4dba31b1-e6fe-4dcb-adb8-47688fea6f12 resumed (18 turns, $2.48). It wrote each answer into the PRD:
    AC-005.1, AC-007.3 to AC-007.5, T-002.2 (60 words) and T-002.3 (threshold 1.0), T-011.1 (0.75, 3 runs), and
    AC-009.1 (four code blocks in order). No `[NEEDS CLARIFICATION]` is left, §13 reads `None.`, and lint gives
    `prd-lint-exit=0`.
  - **It stopped at phase 4,** asking for each of A-01 to A-11 and the two registry rows to be confirmed or
    corrected. Only A-01 (the profile) is a routine stop. A-02 to A-11 are content conventions, so the stop went
    back to the owner:
    - A-02: the only level-2 headings are the four sections;
    - A-03: a term counts as used as a whole word with exact case outside code blocks, and inline code counts;
    - A-04: Requisitos and Problemas comunes are bulleted lists;
    - A-05: a code block is a fenced block (``` or ~~~) holding one line, the command or `Hello, Mundo!`, with any
      info string or none;
    - A-06: the checks parse as CommonMark 0.31.2 after NFC, with `markdown-it-py` in `commonmark` mode (the pack's
      default);
    - A-07: each code block of Instalación and Primera ejecución sits inside its numbered item, indented;
    - A-08: the guide has only those four code blocks, so no step checks or installs Python;
    - A-09: the tests live in `tests/checks/` and `tests/judged/`, because `tests/unit/` holds the CLI's;
    - A-10: changing the guide's path, a section's name or order, or a command the reader runs is a major change;
    - A-11: the `cd` step's sentence names the placeholder `ruta/de/tu/copia/de/greet`;
    - §5 markdownlint `declined`, and §6 `superpowers:writing-plans` `recommended`.
- **P1c**, the owner's confirmation. Ivan's words, relayed by the coordinator: "confirm all", covering A-01 to A-11
  and both registry rows. Sent as `Confirmo A-01 a A-11 y las dos filas.` (the wording I recommended, which carries
  his "confirm all").
  - Session 4dba31b1-e6fe-4dcb-adb8-47688fea6f12 resumed (38 turns, $3.70). It confirmed the assumptions and ran
    phases 5 and 6.
  - **Dry run 1 failed.** The sample was T-003.1, T-004.1, T-007.1, T-008.1 and T-008.3, all `checks` (after P1b the PRD has
    23 cases: 20 `checks`, and 3 `judged`, T-002.3, T-010.1 and T-011.1).
  - The state check passed and the directory was deleted. The tester's 5 questions had no exact-quote dismissal.
    All of them concern what text the `checks` rules compare, which the pack's default (CommonMark after NFC; the
    section rule) does not fix.
  - The PRD went back to `Draft`, the questions are markers in `testing.md`, and lint is 0.
  - **Round 2 (R2-1 to R2-4), the owner's (answered in P1d):**
    - **R2-1:** what "the text" is. A (recommended): the parsed text, not the Markdown source. Plain text, link text
      and inline code count; link URLs, HTML and emphasis markers do not; a soft line break is a space; a heading is
      stripped. B: the Markdown source, line by line.
    - **R2-2:** what a "whole word" is. A (recommended): no Unicode letter, digit or `_` on either side. B:
      surrounded by spaces or sentence punctuation.
    - **R2-3:** indented code blocks. A (recommended): they are code blocks under every rule, so AC-009.1 fails on
      one more. B: they are text.
    - **R2-4:** nested list items. A (recommended): an item's text includes its nested items', and each nested item
      also counts alone. B: an item holds only its own paragraphs.
- **P1d**, the owner's answer, sent verbatim: `R2: 1A 2A 3A 4A` (Ivan: "R2: 1A 2A 3A 4A.  Yes, use the commonmark
  structures").
  - Session resumed (30 turns, $5.90). **Dry run 2 failed:** the sample T-012.1, T-006.3, T-008.1, T-001.1 and
    T-007.5 was all `checks`, and 6 questions had no quote.
  - It opened round 3, R3-1 to R3-5: whitespace for word counts, the text of a list item with several blocks, image
    alt text, which item is a step "after" the curl step, and level-2 headings inside a list or blockquote.
- **Ivan's leave for P1** (relayed by the coordinator): "A later clarification or dry-run question that is purely
  about how the guide is parsed or compared may be answered by you, as the owner, with whatever CommonMark's own
  structure gives under Ivan's rule "Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto
  exacto." That covers what text, word or line a check reads, and how a block, list or heading is delimited." A
  content question still goes back to him, and so does any question I am unsure is parsing-only.
- **P1e**, round 3, answered under that leave: `R3: 1A 2A 3B 4A 5A. 3B porque en CommonMark el texto plano de una
  imagen es su texto alternativo. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.`
  - 1A: Unicode whitespace splits words. 2A: blocks stay separate. 3B: an image's plain text is its alt text, which
    was also the owner's 0.8.0 P1l answer. 4A: a step is an item of the same top-level list. 5A: a heading inside a
    container is that container's.
  - Session resumed (31 turns, $6.90). **Dry run 3 failed:** the sample T-006.3, T-002.2, T-008.3, T-004.1 and
    T-008.1 was all `checks`, with 5 questions.
  - It opened round 4, R4-1 to R4-4: "level-2 heading" across the PRD, "exactly one paragraph", nested lists, and
    the word-character class.
- **P1f**, round 4, answered under the leave: `R4: 1A 2A 3A 4B. 4B porque CommonMark solo distingue espacio en blanco
  Unicode y puntuación Unicode; una marca combinante (M*) es parte de la palabra. Sigue CommonMark; normaliza a NFC
  antes de comparar; en lo demás, texto exacto.`
  - 1A: only top-level headings delimit sections. 2A: one top-level block, a paragraph, as the owner's 5A says. 3A:
    a nested ordered list is an ordered list. 4B: CommonMark's character classes.
  - Session resumed (34 turns, $7.92). **Dry run 4 failed**, but its sample held the judged **T-010.1** (with
    T-006.1, T-007.2, T-005.2 and T-002.1).
  - The judged test called `prd_judge.py` and asserted only its exit code. One question was dismissed by quote; the
    other three reduce to two gaps.
  - It opened round 5:
    - **R5-1:** the four command and output blocks must be fenced, while an indented block still counts as code
      elsewhere (A), or either kind is allowed (B). This is parsing, and the confirmed A-05 already gives A.
    - **R5-2:** a "step". A: Instalación and Primera ejecución each hold exactly one top-level numbered list, a step
      is its direct item, every code block of the section sits inside a step, and the glossary, AC-006.1 and AC-007.1
      are reworded to say so. B: any numbered item at any depth, and several lists allowed.
    - R5-2 limits the guide's form and rewrites ACs, so it is not clearly parsing-only. It went to the owner.
- **P1g**, the owner's answer, sent verbatim: `R5: 1A 2A` (Ivan: "R5: 1A 2A (1 more run)", which caps P1 at this
  dry run).
  - Session resumed (43 turns, $9.12). It applied R5. **Dry run 5 failed:** the sample T-007.2, T-003.1, T-005.1,
    T-006.1 and T-008.2 was all `checks`. The state check was clean, but 3 questions had no quote.
  - Round 6 (R6-1 to R6-3) was asked, and left unanswered because of the cap:
    - **R6-1:** whether the four requirements sit one per direct item of a single top-level bullet list.
    - **R6-2:** the text of a list item that holds a blockquote.
    - **R6-3:** whether the symptoms must be inline code. As plain text, CommonMark reads `<name>` in
      `usage: greet <name>` as raw inline HTML, which is not text, so T-008.2 would fail on a correct guide.
  - The session stopped there. Its last state is `runs/p1-after-P1g.tgz`: Draft 0.1.0, `language: es`, 24 Spanish
    ACs (`- AC-001.1 La guía deberá ser el archivo Markdown `docs/guia/instalacion.md`.`), and
    `prd-lint-exit=0`. Nothing was committed.

### P1 judgment

| Clause (0.8.0 spec §13 P1, as written) | Result |
|---|---|
| "lint exits 0 with Spanish ACs" | **Met.** `prd-lint-exit=0` on the Draft after every round, `language: es`, and every AC opens with a Spanish subject and `deberá`. |
| "the dry run passes with judged T-ids in its sample" | **Not met.** All five dry runs failed. |
| "`/prd-build` writes the guide" | Not reached. |
| "the `checks` and `judged` levels pass, with `.prd-judge/` records showing every median at or above its threshold" | Not reached. |

**Dry run 4 does not meet the judged-T-id clause.** The clause is one sentence, "the dry run passes with judged
T-ids in its sample": the dry run that passes must hold them. Dry run 4's judged test for T-010.1 was right (it
called `prd_judge.py` and asserted its exit code), but the run itself failed on its `checks` questions. The forced
dry run Ivan allowed ("yes to a forced dry run") was for a passing dry run that samples no judged T-id. No dry run
passed, so none was forced.

**The rounds:**

| Dry run | Sample | Judged in sample | Result | The questions' class |
|---|---|---|---|---|
| — (round 1) | — | — | — | content: the terminal in Requisitos, the `cd` step, the output block, the intro paragraph, the style rubric |
| 1 (P1c) | T-003.1, T-004.1, T-007.1, T-008.1, T-008.3 | none | fail, 5 questions | what text a check compares: parsed or source, whole word, indented code, nested list items |
| 2 (P1d) | T-012.1, T-006.3, T-008.1, T-001.1, T-007.5 | none | fail, 6 | whitespace and encoding for word counts, the text of a multi-block list item, image alt text, list order ("after"), headings inside containers |
| 3 (P1e) | T-006.3, T-002.2, T-008.3, T-004.1, T-008.1 | none | fail, 5 | the scope of "level-2 heading", what "one paragraph" counts, nested lists, the word-character class |
| 4 (P1f) | T-006.1, T-007.2, T-010.1, T-005.2, T-002.1 | T-010.1 (test correct) | fail, 4 (1 dismissed by quote) | which block type the commands use, what a step is |
| 5 (P1g) | T-007.2, T-003.1, T-005.1, T-006.1, T-008.2 | none | fail, 3 | list-item placement, the text of an item holding a blockquote, inline HTML in a symptom |

Every dry-run question is about how a `checks` test reads the guide, and none is about a judged case. 0.8.0 failed
the same clause after eight dry runs. **Follow-up, for a later release and not a 0.8.1 task:** a spec line that
fixes, in the `document` pack's Harness default, what text a check compares. That is CommonMark's plain text of
each block, how nested blocks, list items and inline HTML contribute, and the word boundary.

## Findings

| ID | Finding | Disposition |
|---|---|---|
| F-1 | `prd_change.py approve` (through `prd_gates.py answer`) refused every approval in a vendored repo. `change_approve._commit` passed `:(exclude)<prd>/.prd-review.json` to `git add`, and git exits 1 on a pathspec that names an ignored file, even an exclude one. `prd_hooks.py`'s `_ignore_record` ignores that file in every vendored repo, but the test fixture's `.gitignore` did not. A failed add also left what it had staged in the index, because only a failed commit was reset. | Fixed in 6edbb46: the exclude is left out of `git add` when `git check-ignore` says the verdict is ignored (git skips it anyway), and a failed add is unstaged. `test_the_commit_when_the_verdict_is_git_ignored` and `test_a_failed_add_leaves_the_index_and_the_tree_as_they_were` failed first (`refused: git add failed: The following paths are ignored …`, and four staged paths), then passed. Re-vendored in 7b2f7de. `scripts/ci-local.sh origin/main`: 5 jobs pass (2552 passed, 1 skipped; integration 50). Not lint-cli. |

**Scaffold defects:** none.

**Harness defects** (not F-n or S-n; not counted against the toolkit):
- M1 attempt 1: the runner narrowed `Bash` for the review session, where the spec names `Bash`. Fixed with
  `TOOLS_ALLOW=exact`.

**Observations:**
- **O-1: a client that narrows `Bash` cannot get a verdict written.** Claude Code's validator refuses a heredoc body
  with a `{` and a `"` under prefix Bash rules, and `reviewing-a-change.md` step 8 prescribes exactly that heredoc
  when Write is not among the tools. With the spec's tools (`Bash` unrestricted) it works. A client that allows only
  `Bash(uv run:*)`-style rules would need Write, or a script that writes the verdict. The spec does not say which,
  so it is not fixed here.
- **O-2: the review's judgment of one item varied between runs.** The same AC-002.1 edit was decided `patch` in
  attempt 1 and `major` in attempt 2. The bump script is deterministic; the judgment it hands the model is not.
- **O-3: the deploy-step question's casing.** The `question` is the step title, then the `Do:` text verbatim:
  `Approve production. read the staging results …`. The lowercase `read` is the runbook's own text. This is
  cosmetic.
- **O-4: the error-class gate's `evidence` is empty** for an entry with no Evidence lines (E-001 from a failed
  deploy). The spec allows at most 20 lines, so this is not a defect.
- **O-5: the `document` pack's parsing default does not settle what text the checks compare.** It fixes the parser
  (CommonMark 0.31.2 after NFC) and the section rule. With those, round 1 asked no parsing question, where 0.8.0's
  dry runs had stalled on headings and fences. But five dry runs in a row still failed on the next layer: plain text
  against source text, word boundaries, how nested blocks and list items join, and inline HTML (rounds 2 to 6
  above). This is the follow-up spec line under P1.

## Parked

- **P1's dry-run clause** fails for 0.8.1. The follow-up is O-5's spec line for a later release, not a 0.8.1 task.
- **O-1** (a verdict writer for a client with narrowed Bash) needs its own spec line.
- **O-2** (the judgment of a `needs judgment` item varies between runs) is noted, and no change is proposed.
- **Carried from 0.8.0 and not in the 0.8.1 spec:**
  - Spanish units in `nfr-bound`, seen again in P1a (FR-012);
  - the route for a stopped build's leftovers (0.8.0 O-3);
  - the reviewer's other parked minors.

## Cost

| Sessions | USD |
|---|---|
| M1 reviews (attempts 1 to 3) | 7.01 |
| Probes of the Bash validator (probe1 to probe3) and the runner smoke test | 6.90 |
| P1a to P1g | 38.08 |
| **Total** | **51.99** |
