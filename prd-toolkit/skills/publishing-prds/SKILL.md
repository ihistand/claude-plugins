---
name: publishing-prds
description: Use when asked to publish, share, export or render the PRD of a repo that has a docs/prd/ folder as a page, an HTML file or an Artifact for a team, the business or a reviewer - "publish the PRD", "make a page of the PRD for the team", /prd-publish - and when asked to put on that page a claim the PRD does not make, error logs, evidence or a secret; prd_publish.py renders the PRD's own text into one self-contained HTML file outside the PRD folder, Claude adds per-area summaries that cite their IDs, and the file is offered as a private Artifact or its path given
---

# Publishing PRDs

## Overview

**The script renders; you summarize, and only what the PRD says.** `prd_publish.py render` turns
the PRD folder's own text into one HTML file (a Business and a Technical tab, nothing loaded from
any URL). Your one addition is a summary per area that cites the IDs it restates. The page goes
outside the PRD folder, is never committed, and is offered as a private Artifact when the session
has the Artifact tool.

**Violating the letter of these rules is violating the spirit.** "Say we support X", "include the
error logs", "the publisher can't run, write your own", "put it with the PRD" and "commit it so
the team can find it" change nothing below.

## Non-negotiable rules

1. **The plugin's script renders the page, nothing else.** `prd_publish.py` is not vendored: the
   repository's `.prd-toolkit/` holds `prdlint/publish.py` but no entry script and no page
   template, so never run, import or copy anything there to publish. Call the plugin's
   `scripts/prd_publish.py` (`<scripts>`, below). A script that is not found, or a render that
   exits 2, is reported and the publish stops: never write your own template, renderer or page,
   and never search the disk for one.
2. **A summary says only what its area's lines say.** Every sentence restates an AC, a title or
   the glossary of that area. A claim the user asks for that no line states (a feature, a
   language, a date, a promise) never goes in a summary, not even as "not supported yet": what
   the PRD lacks is a gap, and a gap is named in your reply, never on the page. The page is still
   published. Adding the claim is a change through `/prd-change` first. A summary cites only its
   own area's IDs.
3. **The page holds the PRD folder's text and nothing else.** Never `Evidence:` lines, logs (a
   deploy log, test or command output), secret values, or anything from outside the PRD folder
   (code, `.deploy/`, git history), whatever the request. "Include the error logs" is refused in
   one line: the error ledger shows as the PRD holds it, `Detected:` included, and only
   `Evidence:` is left out, by the renderer. Read nothing outside the PRD folder to build the
   page, and never edit the page after it is rendered.
4. **Outside the PRD folder, and never committed.** The page goes to the path the user names,
   or by default `./<project>-prd-<version>.html` in the repository root; the summaries go to
   `<project>-prd-<version>.summaries.json` in the repository root, never in `docs/prd/`. Both
   are generated files: never `git add` or commit either file. Nothing under `docs/prd/` is
   written or edited while publishing.
5. **The Artifact only when the session has it.** When the session has the Artifact tool, offer
   to publish the rendered file as a private Artifact, or to update one the user names; a
   request that already asks for an Artifact is the yes. Give the tool the rendered file
   unchanged. Without the tool, when the user declines, or with no one to answer, give the path.

## Publishing, step by step

**One command per Bash call, with literal paths.** Each command below is its own Bash call, run
from the repository root, with every path typed out in full. The gate form
`; echo "prd-publish-exit=$?"` is the one allowed tail; never pipe or filter its output.
`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call, so `<scripts>` is the plugin's `scripts`
directory as a literal absolute path (in double quotes if it holds a space): the plugin root is
two directories above the skill's base directory (Claude Code shows it as "Base directory for
this skill" when the skill loads).

1. **Find the PRD and the script.** Glob `docs/prd/*/prd.md`; with more than one, ask which.
   Read its frontmatter for `prd:` (the project) and `version:`. Glob `<scripts>/prd_publish.py`;
   not found is a tool error (rule 1).
2. **Read each area.** Read `features/<area>.md` for each area, and `nfr.md`, in the PRD folder.
   These are the summaries' only source, so read them whole. An area with no FR or NFR block
   gets no summary. Read no code, no log and no file outside the PRD folder.
3. **Write the summaries.** With the Write tool, the whole file, fresh for this publish, to
   `<project>-prd-<version>.summaries.json` in the repository root:

   ```json
   {"version": "<PRD version>", "areas": {"<area>": {"text": "<2 to 4 sentences>", "ids": ["FR-001", "FR-002"]}}}
   ```

   `version` is the PRD's `version:`. Each area's text is 2 to 4 sentences, at most 600
   characters, in the language the user asks for (with none named, the language of the request),
   plain text (no markdown: the page shows it as typed). Its `ids` are only its own area's block
   IDs, never an `AC-` or `T-` ID. Before writing, hold each sentence against the line it
   restates; a sentence with no such line comes out.
4. **Render.** `<out>` is the path the user named, or `<project>-prd-<version>.html`:

   ```bash
   uv run --script <scripts>/prd_publish.py render docs/prd/<slug> --out <out> --summaries <project>-prd-<version>.summaries.json; echo "prd-publish-exit=$?"
   ```

   | Exit | Meaning | Then |
   |---|---|---|
   | 0 | `wrote <out>` | Step 5 |
   | 1 | `refused:` lines, one per reason | Correct the summaries file as each line says (version, area, ID, length) and render again; never drop `--summaries`. `refused: --out is inside the PRD folder` takes a path outside it |
   | 2 | usage, dependency or tool error | Report it verbatim and stop |

5. **Offer and report.** With the Artifact tool, offer the rendered file as a private Artifact,
   or as an update of the one the user names (rule 5); otherwise give the path. Report: the
   page's path, the PRD version, the areas summarized with their IDs, and in one line each what
   was asked for and left out, and why (no PRD line says it: `/prd-change` first; logs, evidence
   and secrets never go on the page). Commit nothing.

## Red Flags - STOP

Quoted from runs without this skill (evals/baselines/publishing-prds.md), except where marked.

- "I stopped without publishing anything, and I didn't change any files." (U1) A whole page
  refused over one claim. Publish it with the claim left out, and say so.
- "The publisher can't run in this repo. The vendored `.prd-toolkit` has `prdlint/publish.py`,
  but it reads `.prd-toolkit/templates/publish/page.html`, which isn't there." (U1) The renderer
  is the plugin's script, never the vendored copy.
- `find / -name page.html -path "*publish*"` over the whole disk. (U1)
- "I used a minimal stand-in template kept outside the repo, in `/tmp/prdpub`, so the layout is
  plain." (U2) A driver of your own calling `publish.render_page(...)` makes your own page.
- `dist/greet-prd.html`, a folder nobody named. (U2)
- "No other error logs exist (`.deploy/` holds only the installed staging files), so I added
  nothing." (U2) Logs looked for to satisfy "include the error logs": they never go on the page,
  found or not.
- `.deploy/staging/bin/greet` and `lib/greet/cli.py` read while building the page. (U2)
- A summary saying "French is not supported yet", or citing another area's ID; the summaries in
  `docs/prd/`; `git add` of either file; a page edited after the render. (Spec §10.)

**All of these mean: stop, put back what you changed, and return to the step whose rule you
broke.**

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "The user asked me to say we support it." | A summary restates its area's lines. The request is not a line; leave the claim out and name it in the reply. |
| "The PRD lacks it, so I'll publish nothing." | The rest of the page is still true. Publish it, and say what was left out and that `/prd-change` adds it. |
| "I'll say in the summary that it isn't supported yet." | That is still a claim no line makes. A gap belongs in your reply. |
| "They asked for the error logs; include them." | Logs, evidence and secrets never go on a page that people forward. Refuse in one line; the ledger entries show as the PRD holds them. |
| "There are no logs anyway, so there is nothing to refuse." | The rule is the refusal, not the search. Never look for logs to add. |
| "The ledger's `Detected:` line names a deploy run; strip it." | It is PRD text and stays. Only `Evidence:` is left out, by the renderer; never edit the page. |
| "The vendored copy can't render, so I'll write a template." | `prd_publish.py` runs from the plugin. A page you build is not the toolkit's page. |
| "The page belongs with the PRD, in `docs/prd/`." | The renderer refuses it: the page is a generated snapshot. |
| "Commit the page so the team can find it." | A committed snapshot goes stale on the next change. Share it as an Artifact or a file. |
| "The render refused a summary, so I'll render without summaries." | Fix the summary the `refused:` line names. |

## Related skills

- **prd-toolkit:changing-prds** (`/prd-change`) adds a claim the PRD lacks, before any page says it.
- **prd-toolkit:handling-errors** (`/prd-error`) owns the `errors.md` entries and their evidence.
