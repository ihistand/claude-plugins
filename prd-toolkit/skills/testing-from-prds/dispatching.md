# When you dispatch prd-tester

For callers only: `prd-toolkit:authoring-prds` phase 6, `prd-toolkit:changing-prds` step 4,
adoption step 4, and building. The tester never reads this file.

You are the caller, not the tester. The guard confines the tester's tool calls, not the code the
harness runs: a `conftest.py` the tester writes can overwrite files when pytest runs. So you check
the repository yourself.

**One command per Bash call, with literal paths.** In headless don't-ask runs, the calls seen
denied were a compound with `rm` (an `rm -rf` chained to another command) and a path built from a
variable or `$(…)`, and one denial can end the run. So each command below is its own Bash call,
and every path in it is typed out in full: paste the path a command printed, never a variable that
holds it. The gate form that follows lint or trace with `; echo "prd-lint-exit=$?"` (or
`prd-trace-exit`) is allowed: it was observed to run in the same sessions.

**A remote harness.** Some harnesses run against a remote system that only sees committed code,
such as LookML `test:` blocks that the remote instance runs. There the tester writes the tests in
`Mode: suite` as usual, but its RESULTS test the remote's old code and do not count. The caller,
never the tester, publishes them as that project's PRD or norms allow: for example, commit on the
feature branch and push, then sync the remote dev workspace; never a deploy. When the push is
outward-facing (a shared remote, a merge request), the caller asks the user first. The caller then
takes a fresh snapshot (step 2) and re-dispatches `Mode: suite` to run them. MCP tools are never in
prd-tester's tools, so a remote API is reached through a Bash harness command, such as pytest
calling the API's SDK.

1. **Pick the dry-run directory** (dry run only): `<first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/`,
   named by the current time, interactive or headless alike. The guard lets the tester write
   under the test roots in every session; a session scratchpad is not used, because a
   subagent's `scratchpad_dir` is not known to match yours. Before the dispatch, delete every
   stale `.prd-dry-run-*` directory under the test roots (a run that stopped before its cleanup
   step leaves one), so the tester sees no earlier run's tests. The directory is safe inside a
   test root because no harness command runs during a dry run, and the directory exists only
   between the dispatch and your judgment of the report (step 6 deletes it).
   To find stale ones, Glob `<first test root>/.prd-dry-run-*/**` (or run `ls -a <first test root>`),
   then delete each directory it shows with its own call, `rm -rf <first test root>/.prd-dry-run-<that timestamp>/`.
2. **Record the state** in a new directory outside the repository, `<SNAP>`, after step 1's
   deletions. Run `mktemp -d` as its own call (or use your scratchpad), and paste the path it
   prints wherever `<SNAP>` appears below. Then run each line as its own call:

   ```bash
   git status --porcelain --untracked-files=all > <SNAP>/status-before.txt
   find docs/prd/<slug> -type f > <SNAP>/prd-files-before.txt
   sort -o <SNAP>/prd-files-before.txt <SNAP>/prd-files-before.txt
   GIT_INDEX_FILE=<SNAP>/index git add -A
   GIT_INDEX_FILE=<SNAP>/index git write-tree > <SNAP>/tree-before.txt
   ```

   The temporary index never touches the real one. Its tree records the content of every file
   that is not git-ignored, the PRD folder's included, so it catches a change to a file that was
   already dirty, which `git status` alone would not show. The file list catches a file added
   under the PRD folder even when it is ignored. An edit to a file that was already in the PRD
   folder and is git-ignored is not caught; PRD files are tracked by design.

   Before a suite, check that the harness's own caches, `.pytest_cache/` and `__pycache__/`, are
   git-ignored, or that the harness command does not write them (`-p no:cacheprovider` turns off
   pytest's cache; bytecode written beside imported source needs the ignore). Otherwise the run
   writes them outside the test roots and they fail step 4.
3. **Dispatch** the `prd-toolkit:prd-tester` agent (Agent tool) with this prompt, slots filled,
   and nothing else: no summary of the PRD, no hints, no answers.

   ```
   Mode: <dry run | suite>
   PRD: docs/prd/<slug>/
   Dry-run directory: <first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/   (dry run only)
   T-ids (one per line, each with its test-case file, as --sample-tids prints them):
   <T_IDS>
   ```

   Dispatch with the Agent tool; under `claude --agent` the `skills:` preload does not load.
   A dry run's T-ids are the ones `--sample-tids` printed. A suite's T-id list is every non-unit
   T-id in `test-cases/<area>.yaml`, which the caller reads; `--sample-tids` is for dry runs only.

   Only when `prd-toolkit:prd-tester` is not in the Agent tool's list, a dry run falls back to
   `${CLAUDE_PLUGIN_ROOT}/skills/authoring-prds/dry-run-prompt.md` with a general-purpose agent,
   the same dry-run directory in its `<SCRATCH_DIR>` slot; record the run as unguarded. A suite
   has no fallback: report it as not run.
4. **Check the state** after the tester returns: run the same five commands into `-after`
   files, each its own call (`git add -A` brings `<SNAP>/index` up to date), then each of these:

   ```bash
   diff <SNAP>/status-before.txt <SNAP>/status-after.txt
   diff <SNAP>/prd-files-before.txt <SNAP>/prd-files-after.txt
   ```

   Read `<SNAP>/tree-before.txt` and `<SNAP>/tree-after.txt` (one SHA each), and run
   `git diff --name-only <tree-before SHA> <tree-after SHA>` with the two SHAs pasted in.

   A dry run's check exempts only the run's own `.prd-dry-run-<YYYYMMDDTHHMMSS>/`: any other
   changed path, inside a test root or not, fails it. A suite's check exempts the test roots.
   Anything else changed (the PRD folder, source, config) **fails the run**, whatever the report
   says. Report the changed paths to the user and restore nothing automatically: the user decides
   what to keep.
5. **Judge the report.** A dry run passes on the triage and pass terms in
   `${CLAUDE_PLUGIN_ROOT}/skills/authoring-prds/dry-run-prompt.md` (below its prompt block):
   every question dismissed by an exact quote, TESTS complete, FILES READ inside the PRD folder
   and the run's own dry-run directory, HARNESS CHOICES that change no assertion. A suite also
   needs one RESULTS line per dispatched T-id; each `fail` becomes a change request
   (`prd-toolkit:changing-prds`) or an `E-nnn` candidate for `errors.md`.
6. **Delete the run's directory** (dry run only) once the report is judged, pass or fail, and
   also when the integrity check failed: `rm -rf <first test root>/.prd-dry-run-<YYYYMMDDTHHMMSS>/`,
   alone in its call, the path typed out. It is the tester's own output, not a restore, so step
   4's "restore nothing" does not cover it. Never leave it for the next run. `<SNAP>` is outside
   the repository and holds only the state record: leave it (the system's temporary-file cleanup
   removes it), or delete it with one `rm -rf <SNAP>` call, the path typed out.
