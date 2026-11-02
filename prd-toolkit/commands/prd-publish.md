---
description: Publish the PRD as one self-contained HTML page with prd_publish.py, with per-area summaries that cite their IDs, outside the PRD folder and never committed, offered as a private Artifact (prd-toolkit)
---

Publish the PRD as a page. Arguments, `[<out file>] [<request>]`: $ARGUMENTS

1. Invoke the prd-toolkit:publishing-prds skill first. Read nothing and run nothing before it.
2. Find the one `docs/prd/*/prd.md`. If there is more than one, ask which PRD.
3. A first argument ending in `.html` is the page's path (`--out`); a path inside `docs/prd/` is
   refused, so ask for another. With none, the page goes to `./<project>-prd-<version>.html` in
   the repository root, untracked.
   The rest is the user's request: the audience, the summaries' language, what to stress. A claim in
   it that no PRD line makes is left out of the page and named in the report.
4. Follow the skill exactly, steps 1 to 5, and report as its step 5 says. The page and the
   summaries file are never written into the PRD folder and you never commit either; logs,
   evidence and secrets never go on the page, whatever the request.
