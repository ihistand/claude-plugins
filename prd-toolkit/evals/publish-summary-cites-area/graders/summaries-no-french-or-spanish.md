---
type: regex
pattern: '[Ff]rench|FRENCH|[Ss]panish|SPANISH|[Ff]ran(?:ç|c)ais|[Ff]ranc(?:é|e)s|[Ee]spa(?:ñ|n)ol|[Bb]onjour|\b[Hh]ola\b'
match: not_contains
target: { source: file, path: greet-prd-1.0.0.html }
---

No PRD line mentions French or Spanish, so no summary on the page does, not even as "not supported yet": the
gap goes in the reply. The grader reads the rendered page, since the summaries file is deleted after the render
(R26); the greet PRD's own text names neither. A missing page fails (RED's U1 wrote none).
