# prd-toolkit 0.7 acceptance run

## O-a

Question (carried from 0.5): does a bare `/prd-*` slash command register in a headless `--plugin-dir` run?

Probe, run 2026-11-02 with Claude Code 2.1.316, in a scratch repo built by
`python3 -B prd-toolkit/evals/scaffolds/deploy_repo.py <scratch> ready`:

```
claude -p "/prd-status docs/prd/greet" --plugin-dir <worktree>/prd-toolkit \
  --settings '{"enabledPlugins":{"prd-toolkit@ihistand":false}}' \
  --model sonnet --output-format stream-json --verbose
```

Finding: **the bare command did not register; the namespaced form did.**

- The `init` event's `slash_commands` list (135 entries) held no bare `prd-status`. It held the
  namespaced `prd-toolkit:prd-adopt`, `prd-build`, `prd-change`, `prd-context`, `prd-deploy`,
  `prd-error`, `prd-new`, `prd-publish` and `prd-status`, plus the eight skills as
  `prd-toolkit:<skill>`. The plugin loaded as `prd-toolkit@inline` version 0.6.1.
- The session's first turn was `Skill` with `{"skill":"prd-toolkit:prd-status","args":"docs/prd/greet"}`:
  the model mapped the bare text onto the namespaced command, which expanded to the status prompt.
  It then ran `uv run --script .prd-toolkit/prd_status.py docs/prd/greet` (exit 0) and printed the report.
- So `/prd-status` worked end to end, but through the `prd-toolkit:prd-status` skill call, not as a
  registered bare command. The README's headless note (Task 12) should give the
  `prd-toolkit:<command>` form.
