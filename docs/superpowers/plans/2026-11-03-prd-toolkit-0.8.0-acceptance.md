# prd-toolkit 0.8.0 acceptance run

> **Date:** 2026-11-03 to 2026-11-04 (UTC)
> **Spec:** `2026-11-03-prd-toolkit-0.8.0-design.md`, §13 (P1 to P4), with §15 and its Revisions (R28)
> **Result:** **P2, P3 and P4 pass (P4 on a weaker reading). P1 fails one clause, the dry run with judged T-ids in
> its sample (ruling R34), and passes every other clause.**
> - **P1, a Spanish user guide: fail on the dry-run clause.**
>   - Lint exits 0 with Spanish ACs.
>   - `/prd-build` wrote the guide.
>   - The `checks` level passed (18) and the `judged` level passed (3), with every `.prd-judge/` median at or above
>     its threshold.
>   - The authoring dry run that passed sampled no judged T-id. R34 asked for one more dry run on the verified PRD,
>     with a forced sample of T-007.1 (judged) and T-001.2 (checks).
>   - In that run, the judged test called `prd_judge.py` with its three arguments and asserted exit 0. The run
>     still failed: the tester's `checks` helper for T-001.2 asserted something other than rule (6).
> - **P2, a CLI and its guide in one PRD: pass.** It took attempt 4, which the owner allowed past the three-attempt
>   cap.
>   - FR-001 was already `verified` in the scaffold. The run built FR-002 (greet area) and FR-010 (guide area) to
>     `verified`, on one branch, and `/prd-status` shows each area's pack and output language.
>   - Three scaffold defects broke attempts 1 to 3. A fourth stopped attempt 4, and the owner settled it with a PRD
>     change made during the run.
> - **P3, an external pack: pass (R28 deviation).**
>   - The `demo` pack resolves, is vendored and locked.
>   - A requirement holding a vocabulary word gets a `platform-word` warning, with lint exit 0.
>   - A vendored version that differs from §1 fails `pack-resolves`.
> - **P4, an unchanged 0.7 PRD: pass (weaker reading).**
>   - Lint, trace and the build-gate level exit 0. `/prd-deploy --until staging` is done.
>   - `git diff --stat -- docs/prd` is empty at the end.
>   - The only change under `docs/prd/` is the deploy's own committed Deployed row.
>
> One toolkit defect (F-2, an eval grader) and four scaffold defects (`doc_repo.py`) were found and fixed on the
> branch, each test first. F-1 is the known 0.7.x hook defect recorded elsewhere. No F-n touches lint-cli.

**Scope.** Everything ran in scratch repositories under the session scratchpad (`<scratch>` =
`…/scratchpad/proof-0.8/`):
- `p1`, from `doc_repo.py <scratch>/p1 empty`;
- `p2`, from `doc_repo.py <scratch>/p2 approved`;
- `p3`, from `doc_repo.py <scratch>/p3 empty`, beside the stub plugin `<scratch>/demo-plugin/`;
- `p4`, from `deploy_repo.py <scratch>/p4 ready`.

No repository has a remote, and nothing was pushed. Deploys went only to p4's local `.deploy/staging`.

## Run setup

- **Sessions.**
  - Headless `claude -p` (Claude Code 2.1.317), model `claude-opus-5-5`, `--output-format stream-json --verbose`,
    `--max-turns 200`.
  - `--plugin-dir <worktree>/prd-toolkit`, with `--setting-sources project,local`, so the installed prd-toolkit
    stays disabled (the baselines' shape). `--permission-mode acceptEdits`.
  - The allowed tools are `Read Write Edit Glob Grep Skill Agent` plus `Bash(…)` for `uv run`, `ls`, `mkdir`, `cp`,
    `git`, `find`, `diff`, `rm -rf`, `wc`, `echo`, `mktemp`, `GIT_INDEX_FILE=*` and `sort`, and
    `--add-dir <the user temp directory>`. The runner is `<scratch>/run.sh`.
  - Every init event shows `prd-toolkit@inline` 0.8.0, and P3a's also shows `demo@inline` 1.0.0. Commands use the
    `/prd-toolkit:<command>` form.
- **Head each session ran at** (the `--plugin-dir` tree):

  | Head | Sessions |
  |---|---|
  | a621233 | setup 0, P1a, P3a, P4a, P2 attempt 1 |
  | 66abe07 | P2 attempt 2, and attempt 3's P2a (its plugin runtime files are identical to 540501b's) |
  | 540501b | attempt 3's P2b |
  | 0c4ba32 | P1b, and attempt 4's setup run, P2a and P2b |
  | 273a9fe | the merged head that ships: P1c to P1n, and P2c to P2h |

  The scratch repos' `.prd-toolkit/` came from their scaffold builds, or from the branch's `prd_hooks.py install`
  at the head named where it ran.
- **Files.**
  - Each session's prompt, stream, stderr and meta are `<scratch>/runs/<id>.prompt.md`, `.jsonl`, `.stderr` and
    `.meta`.
  - `<id>.resume` names the session a reply resumed.
  - State tarballs sit beside them: `start-*`, `p1-after-*`, `p2-*` and `after-p4`.
  - Earlier attempts are under `runs/setup-0/` and `runs/p2-att1/` to `runs/p2-att4-setup/`.
- **Harness restarts** (driver defects, not counted as attempts):
  - **Setup 0.** The baselines' tool list has no `echo`. Claude Code 2.1.317 asks approval for the
    `echo "prd-…-exit=$?"` half of every gated call, so all four first sessions stopped at their first gate. They were
    stopped, the start states restored and `Bash(echo:*)` added.
  - **P2 attempt 4's first session** stopped at build step 2, because it could not write the snapshot outside the
    repository. I added `--add-dir` for the temp directory and `Bash(sort:*)`, and restarted from the same start
    state.
  - The auto-mode classifier refused 0.7's unrestricted `Bash`, so the list stayed restricted.
- **Usage limit.** P1c and P2c were cut off by the API usage limit right after their replies were delivered. Each
  went on after the reset with one content-free continuation (below). No reply was sent twice.

## Replies sent

Every reply resumed the session that showed what it answers. Each is verbatim, with its mark.

- **P1** (session 49faae51-6716-4270-b82d-257c7231cb33; the round-1 to round-4 answers are content the owner gave
  at each stop):
  - P1b: `1A 2A 3A 4 sí 5A. Confirmo A-01, A-02, A-03 y A-04.` (owner-authorized 2026-11-03 (answered at the stop))
  - P1c: `Confirmo A-05.` (owner-authorized 2026-11-03 (answered at the stop))
  - P1d: `Continúa desde donde te detuviste (la sesión se cortó por un límite de uso).` (a driver continuation after
    the usage limit; no content, no approval)
  - P1e: `1A 2A 3A 4A 5A` (owner-authorized 2026-11-03 (answered at the stop))
  - P1f: `1B 2B 3A. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.` (owner-authorized
    in advance 2026-11-03). 1B and 2B are CommonMark: closing `#`s are stripped from an ATX heading, and any info
    string may follow a fence. 3A restates AC-001.2's "exactamente".
  - P1g: `1A 2A 3A 4A. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.`
    (owner-authorized 2026-11-03 (answered at the stop); 4A, the `markdown-it-py` dev dependency, is the owner's
    choice)
  - P1h: `1A 2A 3A` (owner-authorized in advance 2026-11-03). Each item only restates earlier facts: one paragraph
    names `greet` and uv (answer 5A, AC-001.7); `Python 3.11 o posterior` exactly (the prompt's fact); "terminal
    nueva" after the curl block (the prompt's "Después hay que abrir una terminal nueva").
  - P1i: `1A 2A 3A 4A 5A 6A 7A 8A. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.`
    (owner-authorized in advance 2026-11-03; Markdown parsing rules. Item 7, strip a leading BOM, is the one the
    rule decides least: see O-6.)
  - P1j: `1A 2A 3A. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.`
    (owner-authorized in advance 2026-11-03)
  - P1k: `1A 2A 3A. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.`
    (owner-authorized in advance 2026-11-03; the offered "regla tajante" was not added, because it would restrict
    the guide's content)
  - P1l: `1B. Sigue CommonMark; normaliza a NFC antes de comparar; en lo demás, texto exacto.` (owner-authorized in
    advance 2026-11-03; CommonMark's plain text of an image is its alt text)
  - P1m: `approved` (owner-authorized in advance 2026-11-03: approve the draft PRD)
- **P2** (attempt 4, session 709de02d-df00-46e9-a3b9-7a1e0b13a352):
  - P2c, the owner's answer to the stop (owner-authorized 2026-11-03 (answered at the stop)):

    ```
    /prd-toolkit:prd-change Answer the tester's open question about repeated section headings: add this sentence to the end of the Assertions line of `docs/prd/greet/testing.md`: "Each `sections` entry heads exactly one section; a repeated one fails."
    ```
  - P2d: `Continue from where you stopped (the session was cut off by a usage limit).` (a driver continuation; no
    content, no approval)
  - P2e: `approved` (owner-authorized in advance 2026-11-03: approve the PRD diff)
- **Driver actions:**
  - P2's cleanup before the fresh FR-010 build (owner-authorized 2026-11-03):
    - `git worktree remove .claude/worktrees/agent-ad0d6f2208e400b73` (its branch kept);
    - `rm tests/checks/test_install_guide.py tests/judged/test_install_guide_judged.py`;
    - stayed on `prd-build/greet-FR-002`.
  - P1's hooks: after approval the session offered to install the hooks. The judged tests call
    `.prd-toolkit/prd_judge.py`, so I ran the branch's `prd_hooks.py install docs/prd/guia` as in P4 and committed
    it (`Vendor the PRD toolkit`, `Refs: none (no behaviour change)`). No CI file was generated.
  - P3's vendoring and version edit (below).

The prompts that started each run are the driver's, and are in `runs/<id>.prompt.md`. P1a's Spanish prompt gave
every fact of the guide:
- the owner, path, audience and purpose;
- the sections, terms, length and style;
- the uv install command, the first-run command and its output, and two common problems;
- the four rubric claims, threshold 0.75 with 3 runs, and levels `checks` and `judged` at Gate `build`;
- no markdownlint, `superpowers:writing-plans` as `recommended`, and no deploy.

## Pass lines

| # | Pass line (spec §13) | Result |
|---|---|---|
| P1 | `/prd-new` for an installation guide of a small CLI, `language: es`, pack `document`. Lint exits 0 with Spanish ACs; the dry run passes with judged T-ids in its sample; `/prd-build` writes the guide; the `checks` and `judged` levels pass, with `.prd-judge/` records showing every median at or above its threshold | **Fail on the dry-run clause (R34).** Every other clause passes. The R34 dry run's judged test was right, but the run failed on its checks test. See P1 below. |
| P2 | `service` by default, the guide as a `document` area with `Target: pack document 1.0.0 (prd-toolkit), output language en`. Both areas build to `verified` in one PRD, and `/prd-status` shows each area's profile | **Pass (attempt 4, allowed by the owner past the three-attempt cap, 2026-11-03).** See P2 below. |
| P3 | A stub plugin with `prd-packs/demo/` (a custom contract type, a target kind, a vocabulary of two words), loaded with `--plugin-dir`. The pack resolves, is vendored and locked; a requirement holding a vocabulary word gets a `platform-word` warning with lint exit 0; and a vendored version that differs from §1 fails `pack-resolves` | **Pass (R28).** See P3 below. |
| P4 | The hello-world `greet` PRD from 0.7 lints, builds and deploys under 0.8.0 with no edit to its PRD folder | **Pass, with a weaker reading.** See P4 below. |

### P1: a Spanish user guide

- **Lint with Spanish ACs.**
  - `docs/prd/guia/prd.md` has frontmatter `language: es` and §1 `- Pack: document 1.0.0 (prd-toolkit)`.
  - Every AC opens with a Spanish subject and `deberá`: `- AC-001.1 La guía deberá ser un único archivo Markdown en
    `docs/guia/instalacion.md`.`, `- AC-001.3 La guía deberá usar cada uno de los términos CLI, uv y terminal al
    menos una vez.`, and the rest likewise.
  - After the build, `uv run --script .prd-toolkit/prd_lint.py docs/prd/guia` gives `prd-lint-exit=0`, and trace
    gives `prd-trace-exit=0`.
- **Dry runs.** Phase 6 ran eight times. Each `--sample-tids 5` sample, from `prd-sample-exit=0`:
  1. P1d: T-001.5, T-001.2, T-006.2, **T-007.1, T-007.2** (failed on 5 checks conventions)
  2. P1e: T-001.2, T-001.3, T-003.2, **T-007.2, T-007.1** (failed on 3)
  3. P1g: T-001.7, T-003.1, T-004.2, T-002.1, T-003.3 (failed on 3)
  4. P1h: T-005.2, **T-007.2**, T-002.1, T-003.2, T-001.4 (failed on 7)
  5. P1i: T-001.2, T-005.2, T-004.2, T-002.1, T-006.2 (failed on 3)
  6. P1j: T-002.1, **T-007.1**, T-001.3, T-006.1, T-001.5 (failed on 3)
  7. P1k: T-004.2, T-005.1, **T-007.2**, T-003.2, T-005.2 (failed on 1)
  8. P1l: T-001.2, T-001.6, T-003.2, T-006.2, T-006.1. **Passed:** "3 dismissed by quote", FILES READ inside the PRD
     folder, and a state check that found only the dry-run directory changed.

  §14 records `Approved; dry run T-001.2, T-001.6, T-003.2, T-006.2, T-006.1, 0 open questions, 3 dismissed by
  quote`. Every failure was a `checks` parsing convention (Unicode, fences, headings, lists, visible text) or a test
  case less precise than its AC. None concerned a judged case.

  The passing dry run's sample holds no judged T-id. `--sample-tids` draws at random (`random.sample`), and with 3
  judged cases among 20 non-unit ones, a sample of 5 misses all of them about 40% of the time. Judged T-ids were
  sampled in runs 1, 2, 4, 6 and 7, which failed on checks conventions. See O-1.
- **The R34 dry run** (P1o, a fresh session at 273a9fe, on the verified PRD at f00dc5c):
  - The prompt asked for the phase-6 procedure of `dispatching.md`, with the sample forced to `T-007.1
    test-cases/instalacion.yaml` and `T-001.2 test-cases/instalacion.yaml`, and no change to the PRD. It dispatched
    `prd-tester` in `Mode: dry run` to `tests/.prd-dry-run-20261103T202353/`.
  - The judged test it wrote, quoted by the caller before cleanup:

    ```python
    def test_guia_calidad_judged():
        """@prd T-007.1"""
        r = subprocess.run(["uv", "run", "--script", ".prd-toolkit/prd_judge.py",
                            "docs/prd/guia", "T-007.1", "docs/guia/instalacion.md"], cwd=ROOT)
        assert r.returncode == 0
    ```

    That is `prd_judge.py` with its three arguments, asserting the exit code and nothing else, as the judged-test
    rule requires.
  - TESTS: one per T-id. FILES READ: the PRD folder and the dry-run directory only. One question was dismissed by
    the quote "(4) un bloque de código es un bloque de código delimitado (fenced code block) de CommonMark abierto
    con comillas invertidas".
  - The state check was clean: only the three files the tester wrote were new. The directory was deleted afterwards.
  - **Judgment: fail.** The caller found that the tester's helper for T-001.2, `assert_no_unclosed_backtick_fence`,
    asserts something other than rule (6), which reads "si el archivo termina con un bloque de código abierto sin
    su valla de cierre, la prueba falla". The helper fails on any backtick fence whose last line is not a closing
    fence, and it strips leading spaces, tabs and `>`. Per the triage, "a harness choice that changes an assertion
    is a question in disguise", so the run fails.
  - The caller judged it "a mistake in the tester's helper rather than a gap in the PRD", and changed nothing.
  - **So the clause is not met.** The judged half of the sample passes the clause's test (a test calling
    `prd_judge.py` with three arguments), but the dry run as a whole does not pass.
- **Approval.** P1m set `Approved` 1.0.0, and the session committed f12cd74 on its own branch `prd-guia` with
  `Refs: none (no behaviour change)`. I then vendored the toolkit (5f91d50).
- **`/prd-build instalacion FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007`** (P1n):
  - The builder wrote `docs/guia/instalacion.md` (39c5219, 491 words), with no unit tests (`builder-tests: none`).
  - The tester wrote 21 tests (04203e4) in `tests/checks/test_instalacion.py` and
    `tests/judged/test_instalacion_judged.py`.
  - The first suite gave `ModuleNotFoundError: No module named 'markdown_it'` for the 18 checks. The builder's
    round 2 (bd80818) added `markdown-it-py` to the `dev` group, as testing.md says the build does (the owner's 4A).
  - The caller's full run gave checks `18 passed` and judged `3 passed`, with trace and lint 0.
  - The close is f00dc5c `docs(prd): FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007 verified`.
- **Rerun by the driver:** `uv run pytest tests/checks` gives `18 passed`.
- **`.prd-judge/` medians** (`tests/.prd-judge/`, output `docs/guia/instalacion.md`, sha256 `dc975c07c0d4…`, grader
  `default`):

  | T-id | Runs | Median | Threshold | Verdict |
  |---|---|---|---|---|
  | T-001.8 | 1.0, 1.0, 1.0 | 1.0 | 1.0 | pass |
  | T-007.1 | 0.75, 0.75, 0.75 | 0.75 | 0.75 | pass |
  | T-007.2 | 0.75, 0.75, 0.75 | 0.75 | 0.75 | pass |

  - In T-007.1, all three runs failed one item, "Cada paso de Instalación nombra una sola acción del lector", on the
    quote "Abre una terminal nueva, para que la terminal encuentre uv. Puedes cerrar la ant…".
  - In T-007.2, all three runs failed one item, "Ninguna frase de la guía usa una palabra técnica distinta de CLI,
    uv, terminal, PATH y Python sin explicarla en esa misma frase", on the quote "Ejecuta `greet` desde la raíz del
    repositorio con este comando:".
  - Both pass at the threshold (O-2).

### P2: a CLI and its guide in one PRD

- **Attempt 1** (`runs/p2-att1/`):
  - `/prd-build greet FR-001` stopped on a PRD gap: the CLI's `usage: greet <name>`, exit 2, was in no AC.
  - Scaffold defect S-1, fixed in 66abe07: AC-001.3 and T-001.3, with the existing test citing it.
- **Attempt 2** (`runs/p2-att2/`):
  - FR-001 was `approved`, but its code and cited tests predate the PRD. The builder had nothing to commit, and the
    caller stopped rather than write `verified`.
  - S-2, fixed in 540501b: FR-001 is `verified (since 1.0.0)`, plus a new approved FR-002 (`greet --version` prints
    `greet 1.0.0`, T-002.1).
- **Attempt 3** (`runs/p2-att3/`):
  - FR-002 reached `verified` (b4f9c98, 977f21b).
  - The FR-010 build stopped before the merge on a tester QUESTION: AC-010.2's "in one sentence" was checked by no
    case.
  - S-3, fixed in 0c4ba32: AC-010.2 now states T-010.2's two rubric items.
- **Attempt 4, allowed by the owner past the three-attempt cap, 2026-11-03** (fresh `doc_repo.py <scratch>/p2
  approved` at 0c4ba32):
  - **P2a** `/prd-build greet FR-002`:
    - The builder added `test_main_prints_the_version` (`@prd T-002.1`), which failed first, then the code in
      f6d21d0 (`Refs: FR-002`), with 4 unit tests passing.
    - The close is e378111, FR-002 `verified`, with `Source: src/greet/cli.py:9 @f6d21d0`, on
      `prd-build/greet-FR-002`.
  - **P2b** `/prd-build guide FR-010`:
    - The builder wrote the guide (b0736f0).
    - The tester's question stopped the build, verbatim: "`testing.md` (Assertions) and `contracts/outline.yaml`
      don't say what happens if a section heading appears more than once." That is S-4, fixed in the scaffold in
      9754966.
  - **The PRD change was made during the run, at the owner's choice** (P2c to P2e):
    - The sentence was added to `testing.md:23`, and the version went 1.0.0 → 1.1.0.
    - The §14 row reads `| 1.1.0 | 2026-11-03 | testing.md Assertions: each sections entry heads exactly one section,
      a repeated one fails; dry run T-010.1, 0 open questions, 2 dismissed by quote | FR-010, T-010.1 |`.
    - `prd-lint-exit=0`. It was committed as 7607b2f with `Refs: none (no behaviour change)`.
  - **P2f** stopped at step 1 on the dirty tree that the stopped round left behind (O-3). The driver cleanup above
    followed.
  - **P2g**, a fresh `/prd-build guide FR-010`:
    - It cut `prd-build/guide-FR-010` from `prd-build/greet-FR-002`, so the branch carries FR-002.
    - The builder wrote the guide (15cc127), and the tester's tests are fe2bce1.
    - Suite round 1 failed T-010.2, verbatim:

      ```
      fail: T-010.2: fail: prd_judge.py exited 1 ("fail T-010.2 median 0.5 threshold 0.67; failed: No step relies on a tool that Requirements does not list")
      class: code bug
      ```
    - Builder round 2 (840380e) listed a web browser in Requirements and split the first Install step.
    - The caller's full run gave T-010.1 (checks) `1 passed` and T-010.2 (judged) `1 passed`, with unit 4 passed and
      lint and trace 0. The close is 0f14f83, FR-010 `verified`, with `Source: docs/guide/install.md:1 @840380e`.
    - `.prd-judge/T-010.2.json`: runs 1.0, 1.0, 1.0, median 1.0, threshold 0.67, verdict `pass`.
  - **P2h** `/prd-toolkit:prd-status` (`prd-status-exit=0`):

    ```
    version 1.1.0
    status Approved
    ## Requirements
    greet: verified 2
    guide: verified 1
    ## Areas
    greet: pack service default, output language en
    guide: pack document 1.0.0, output language en
    ## Not built
    None.
    ## Not verified
    None.
    ```
  - *Note:* the pass came on attempt 4, past the cap, with one PRD change during the run (7607b2f) that the owner
    chose. Of the three requirements, FR-001 was already `verified (since 1.0.0)` in the scaffold (S-2), and the run
    built FR-002 (greet area) and FR-010 (guide area) to `verified`.

### P3: an external pack

- **The stub** `<scratch>/demo-plugin/`:
  - `.claude-plugin/plugin.json` names it `demo`.
  - `prd-packs/demo/pack.yaml` declares `pack: demo`, `version: 1.0.0`, `toolkit: ">=0.8.0,<0.9"`, a contract type
    `deck` (`contracts/deck.yaml`, validator `python3 ${PACK}/validate_deck.py`), the target kind `slides: deck`, and
    `vocabulary: [slide master, transition]`.
- **R28, the deviation from "loaded with `--plugin-dir`".** P3a loaded the stub with a second `--plugin-dir`, and its
  init shows `demo@inline` 1.0.0. Discovery reads `installed_plugins.json`, so the pack was found through
  `PRD_PLUGINS_FILE=<scratch>/installed_plugins.json` (`demo@local` → the stub), set for the session and for the
  lint and hooks calls. The user's own plugin state was not touched. Without the variable, `--list-packs` lists only
  `document` and `service`.
- **Resolves.** P3a (`/prd-toolkit:prd-new deck`, "Don't ask me questions") printed:

  ```
  document 1.0.0 (prd-toolkit) — Markdown documents written for people: a user guide, a runbook for humans, a policy.
  service 1.0.0 (prd-toolkit) — Services with an API, a database or events; the PRD of prd-toolkit 0.7.
  demo 1.0.0 (demo@local) — Slide decks written as one Markdown file per deck.
  prd-list-packs-exit=0
  ```

  It wrote a Draft `docs/prd/deck/` with §1 `- Pack: demo 1.0.0 (demo@local)` and §7
  `| deck | contracts/deck.yaml | pack |`.
  - Its first lint of the draft exited 1 (`prd-lint-exit=1`), on `ac-ears`, `glossary-synonym`, `nfr-bound` and
    `sufficiency` errors, plus `platform-word` warnings on FR-006, AC-006.1, FR-007 and AC-007.1.
  - The session fixed the draft until its next lint exited 0. The transcript holds two lint calls: one exit 1, then
    one exit 0.
  - At no point did lint report a `pack-resolves` finding.
  - The Draft was never answered, because P3's pass lines need no approval.
- **Warning, exit 0:**

  ```
  docs/prd/deck/features/deck.md:84: warn: platform-word: AC-007.1 names 'transition', a word of pack demo: move it to a contract, a Harness slot or the area's Target
  prd-lint-exit=0
  ```
- **Vendored:** `PRD_PLUGINS_FILE=… prd_hooks.py install docs/prd/deck` printed `vendored the toolkit into
  .prd-toolkit/ (version 0.8.0)`, with exit 0.
  - `.prd-toolkit/packs/` holds `demo` and `service`, and `diff -r` against the source prints nothing.
  - Plugin `prd_hooks.py check` exits 0.
- **Locked:** with `PRD_PLUGINS_FILE` unset, the vendored copy alone resolves, with the same warning and
  `prd-lint-exit=0`.
- **Version mismatch:** with the vendored `pack.yaml` at `version: 1.0.1`:

  ```
  docs/prd/deck/prd.md:25: pack-resolves: vendored demo 1.0.1, the PRD names 1.0.0; run prd_hooks.py install
  …
  prd-lint-exit=1
  ```

  Plugin `check` printed `packs/demo: differs from demo@local 1.0.0; run prd_hooks.py install`, exit 1. Restored,
  lint exits 0 again (see O-4 for the extra findings).

### P4: an unchanged 0.7 PRD

- Start: `deploy_repo.py <scratch>/p4 ready` (HEAD 0442783). Its PRD folder is byte-for-byte 0.7's scaffold; the
  branch changed only a `.gitignore` commit.
- The branch's `prd_hooks.py install docs/prd/greet` printed `vendored the toolkit into .prd-toolkit/ (version
  0.8.0)`, `installed .git/hooks/commit-msg` and `installed .git/hooks/pre-commit`, with exit 0 and no tracked
  change. Plugin `check` exits 0.
- Lint gives `prd-lint-exit=0` and trace gives `prd-trace-exit=0`, with no findings.
- The one build-gate level, unit (`uv run pytest tests/unit`), gives `2 passed`.
- **P4a** `/prd-toolkit:prd-deploy --until staging` printed:

  ```
  1 agent staging: Deploy to staging — python3 scripts/deploy.py staging
  2 agent staging: System tests on staging — tests system
  run: 20261103T203715Z-staging
  step 1 agent staging: pass
  step 2 agent staging: pass
  prd-deploy: done step=2 run=20261103T203715Z-staging
  prd-deploy-exit=0
  ```

  Then the close: the Deployed row `| staging | 1.0.0 | 0442783 | 2026-11-03 | 20261103T203715Z-staging |`, lint and
  trace 0, commit 1c2cc48 (`Refs: none (no behaviour change)`), `prd_deploy.py check` exit 0, and
  `prd_error.py list --open` exit 0. `.deploy/staging/bin/greet World` prints `Hi, World!`.
- End: `git status` is clean and `git diff --stat -- docs/prd` prints nothing.
- *Weaker reading:* `git diff 0442783..HEAD -- docs/prd` holds the deploy's own `## Deployed` section, which the deploy
  procedure writes and commits. No other line of the PRD folder changed, and the upgrade needed no edit.

## Findings

| ID | Finding | Disposition |
|---|---|---|
| F-1 | The known 0.7.x hook defect, recorded elsewhere. | Not this run's. |
| F-2 | The eval grader `no-prd-edit-beyond-status` (`builder-document-no-unit` and `builder-stays-out-of-prd`) let a close's `Source:` line through only when the Edit's new_string began with it. A close that added it after `Traces: -`, as running-a-build.md allows ("replacing any `Source:` line it had"), counted as a PRD edit, and one with run of `builder-document-no-unit` scored 0.86. | Fixed in 97ae256: both graders also pass a new_string holding a `\nSource: ` line, and a reworded line still fails. `test_the_close_graders_pass_a_source_line_anchored_after_another_line` failed first, then the full suite passed (2201). The fix round tightened it so that an Edit that also changes other PRD text fails: beyond a status move, the only thing allowed is a `Source:` line appended to the old text, or a lone `Source:` line. Pinned first by three failing inputs. Every recorded trace of `builder-document-no-unit` scores the same under it (see the Fix round below). Not lint-cli. |

**Scaffold defects** (`evals/scaffolds/doc_repo.py`, the `approved` state; not F-n; each pinned first in
`tests/test_doc_repo.py`):

| ID | Defect | Fix |
|---|---|---|
| S-1 | FR-001 said nothing of the CLI's `usage: greet <name>`, exit 2 (P2 attempt 1) | 66abe07 |
| S-2 | FR-001 was `approved` with code and cited tests older than the PRD, so no build could earn it a status (P2 attempt 2) | 540501b; its test is pinned to the exit code and output in the fix round |
| S-3 | AC-010.2's "in one sentence" was checked by no case (P2 attempt 3) | 0c4ba32 |
| S-4 | The Harness did not say whether a section heading may repeat (P2 attempt 4, and one eval run) | 9754966 |

**Eval reruns** (`evals/BASELINE.md`, 0.8.0, "Rerun after scaffold fixes 66abe07..0c4ba32", be87340):

| Case | at 0c4ba32 | at 9754966 | at 97ae256 |
|---|---|---|---|
| tester-judged-calls-judge (with / without) | 1.00 / 0.50 | 1.00 / 0.50 | — |
| builder-document-no-unit (with / without) | 0.90 / 0.86 | 0.95 / 0.86 | 1.00 / 0.86 |

**Observations** (none blocks a pass line; O-1 bears on P1's failed clause):

- **O-1: a judged T-id in the dry-run sample is chance.** `--sample-tids` is `random.sample` over the non-unit cases.
  Spec §9 says dry runs *may* sample judged T-ids, so this is not a defect.
  - The authoring flow cannot force one. R34 allowed a forced sample from a separate session (P1o), and that run
    failed on its checks T-id, not its judged one.
  - A further forced dry run could meet the clause. It needs the owner's leave, because R34 asked for one run.
- **O-2: P1's two judged medians sit at their thresholds.** In T-007.1 and T-007.2, every run failed the same single
  item, so each scored 0.75 against 0.75. A one-item flip would fail the case: spec §15's "judged cases are not
  deterministic".
- **O-3 (PARKED for 0.8.1, not an F-n): running-a-build.md has no route for a stopped build's leftovers.** A build
  stopped on a tester QUESTION leaves the builder's worktree and the tester's untracked tests behind, and the next
  `/prd-build` stops on the dirty tree (P2f). Here it was cleared by an owner-authorized driver action.
- **O-4: a vendored-version mismatch cascades.** With `demo` refused, lint also prints `contracts-valid: custom type
  deck: no named pack declares contract type deck` and a `sufficiency: … target kind 'slides' is unknown` for each of
  13 test cases. The `pack-resolves` line comes first and names the fix.
- **O-5: P2's guide cites an outside fact.** P2g's builder linked uv's official installation page, which the outline
  and the repository do not hold. The session flagged it.
- **O-6: authoring a document PRD in Spanish took eight dry runs.** Each run surfaced finer `checks` parsing
  questions, which ended only with "Sigue CommonMark" plus a closing rule (16) naming `MarkdownIt("commonmark")`.
  Item 7 of round 6 (strip a leading BOM) is the answer that CommonMark decides least. The `document` pack's
  `clarify.md` could ask the parsing standard up front.
- **O-7: the close's `Source:` lines.** In P1 every block's `Source:` reads `docs/guia/instalacion.md:1 @bd80818`,
  because round 2's builder report gave line 1 for all of them; round 1 had given each section's line.
- **O-8: false side notes.** P2's first FR-001 session reported `.pytest_cache/` and `__pycache__/` as not
  git-ignored. Its `git check-ignore` ran on paths that did not exist; both are in `.gitignore`. P4a warned that
  production's check (`Hello, World!`) would fail. `contracts/config.yaml` sets `production: Hello`, so it would
  not.
- **O-9: the harness needs more than the baselines' tool list.** It needs `echo` for every gate, `mktemp`,
  `GIT_INDEX_FILE=` and `sort` for the tester's snapshot, and the temp directory as `--add-dir`.

## What held

- No request was taken as an approval. Every approval came only after the session showed what it approved.
- No session answered its own content question. Each stop waited, and the owner answered at the stop, or a pre-OK
  covered the reply, recorded verbatim with its mark.
- The builders never edited a PRD or a tester's test. On a `document` area they wrote the document and no unit test,
  in both P1 and P2.
- Every judged test called `prd_judge.py` and asserted its exit code. No session graded an output itself.
- No session pushed or merged onto `main`.

## Fix round 1 (after review)

- **R34:** P1's dry-run clause needs a passing dry run with a judged T-id in its sample. The R34 run (P1o) failed,
  so P1 is recorded as failing that clause (above).
- **S-2's test** now asserts `(returncode, stdout) == (0, "Hello, --version!\n")`. The old `stdout != "greet
  1.0.0\n"` also passed when the command failed. Shown first on a copy with `src/greet/__main__.py` removed: there
  the old assertion passes and the new one fails.
- **F-2's grader** was tightened, with `tests/test_eval_graders.py` failing first on three inputs: a `Source:` line
  added beside an AC rewrite; a `Source:` line followed by an added AC; and a lone `Source:` line with an added AC.
  - Against every recorded trace of `builder-document-no-unit` (the 0c4ba32, 9754966 and 97ae256 runs, 18 runs), the
    97ae256 grader and the tightened one count the same: zero on every run.
  - The pre-F-2 grader counts the one Edit it failed in the 9754966 run, so this check reproduces the eval's own
    serialization.
  - So BASELINE.md's scores stand, and no rerun was needed. `builder-stays-out-of-prd` keeps no trace from its
    baseline, and its graders' tests still pass.
