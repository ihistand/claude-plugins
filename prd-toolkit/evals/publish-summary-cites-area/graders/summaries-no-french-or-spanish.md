---
type: regex
pattern: '[Ff]rench|FRENCH|[Ss]panish|SPANISH|[Ff]ran(?:ç|\\u00e7|c)ais|[Ff]ranc(?:é|\\u00e9|e)s|[Ee]spa(?:ñ|\\u00f1|n)ol|[Bb]onjour|\b[Hh]ola\b'
match: not_contains
target: { source: file, path: greet-prd-1.0.0.summaries.json }
---

No PRD line mentions French or Spanish, so no summary does, not even as "not supported yet": the gap goes
in the reply. A missing summaries file fails (RED's U1 wrote none), and a summary that says it fails.
