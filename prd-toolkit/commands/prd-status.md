---
description: Print where every requirement of the PRD stands (prd-toolkit)
---

Print the prd-toolkit status report. Arguments: $ARGUMENTS

**Which script.** `${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so no command holds it.
In every command below, `<scripts>` is `.prd-toolkit` when the repository has a `.prd-toolkit/`
directory: that is the copy its hooks and CI run. Otherwise `<scripts>` is the plugin's `scripts`
directory, written as a literal absolute path (in double quotes if it holds a space): the plugin
root is two directories above the skill's base directory (Claude Code shows it as "Base
directory for this skill" when a prd-toolkit skill loads; when none has, load `prd-toolkit:changing-prds`, which is
loaded only to read its base directory: none of its steps are followed), and `<scripts>` is
`<plugin root>/scripts`.
Glob for `.prd-toolkit/*.py` once to decide, and use the same `<scripts>` for every command.
A script that is not found is a tool error: report it, never guess another path.
When `.prd-toolkit/` exists but holds no `prd_error.py`, the vendored copy predates 0.6: stop, and
tell the user to run `prd_hooks.py install docs/prd/<slug>` from the plugin (the README's form)
and commit `.prd-toolkit/`.

1. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
2. Run the script in one Bash call, with the literal PRD folder:
   `uv run --script <scripts>/prd_status.py docs/prd/<slug>; echo "prd-status-exit=$?"`
   Add `--json` only when asked for JSON. Never pipe, filter or truncate the output (no `| head`,
   no `| grep`): `prd-status-exit=` then reports the filter's status, not the script's.
3. Print the output as it is. The report has nine parts: Header, Requirements, Adoption map,
   Not built, Not verified, Open errors, CI, Deployed and Matrix. It is read-only.
4. On `prd-status-exit=2`, the call was wrong and nothing printed: fix the path.
