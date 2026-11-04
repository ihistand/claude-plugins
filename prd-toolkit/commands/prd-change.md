---
description: Change the PRD before changing behaviour (prd-toolkit)
---

Invoke the prd-toolkit:changing-prds skill and follow it exactly. Arguments: $ARGUMENTS

When the arguments begin with `--review <dir>`, this is review mode: read
`${CLAUDE_PLUGIN_ROOT}/skills/changing-prds/reviewing-a-change.md` whole and follow it, not the
skill's five steps. Review mode edits nothing. `<dir>` is the PRD folder, and a `--base <ref>` after
it is the base. Any other words are a request the review answers in its report, never an edit,
whatever they ask for.

Otherwise the arguments are the change to make.
