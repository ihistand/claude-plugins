---
type: regex
pattern: 'ASSUMPTION A-\d|\|\s*A-\d+\s*\||NEEDS CLARIFICATION: (?!(?:activity|components and how they connect; add a mermaid diagram|database and version|does the product have a user interface\? Describe it, or replace this line with `Not applicable: <reason>`|file glob|first domain term|first measurable goal|for each contract listed above, populate its file, or delete the file, drop its row here and add a section 1 line in the form: - Not applicable: \(the file path in backticks\) — \(the reason\)\. contracts\/errors\.yaml is mandatory: always populate it, never delete it|framework and version|how changes roll out|how long old behaviour is kept|its meaning|language and version|linter command|new project, or an existing system to adopt\? Replace this line with `Not applicable: new project.`, or with `See adoption.md.` and put the `\| Area \| State \| Boundary \|` table in adoption.md|repository URL|skill name|technologies ruled out|what counts as breaking|what does this product do, and for whom, in two sentences|what is the first question to settle with the owner|what this PRD deliberately excludes|where it runs|where the rules live|who or what it applies to|who owns this product|who uses it)\])'
target: { source: file, path: docs/prd/link-shortener/prd.md }
---

Unknowns are marked, never silently invented. The grader reads the PRD as written (the prompt names
the slug, so the path is fixed) and needs either a numbered assumption (`ASSUMPTION A-<digit>`, or
a section 12 row `| A-<digits> |`; the template's own `A-nn` has no digit) or a
`NEEDS CLARIFICATION` marker that the template copy and its slot fill do not already hold. The
lookahead lists every marker text in `templates/prd/prd.md` plus the `{{owner}}` fill, "who owns
this product"; `tests/test_eval_graders.py` keeps that list in step with the template.

Hand-made negatives, each checked to fail:
- the template copied verbatim with its slots filled;
- that copy, then an Edit that invents values (`[NEEDS CLARIFICATION: database and version]` ->
  `PostgreSQL 16`, the framework -> `FastAPI 0.115`);
- that copy, then only a read-only `cd docs/prd/link-shortener/ && grep -rn "NEEDS CLARIFICATION" .`,
  which leaves the file as copied.
