---
type: regex
pattern: '## 1\. Metadata & stack(?=(?:(?!\n## 2\.)[\s\S])*?(?:entry[- ]points?|console[- ]scripts?|project\.scripts))|NEEDS CLARIFICATION: [^\]]*(?:entry[- ]point|console script)'
target: { source: file, path: docs/prd/hello/prd.md }
---

The PRD names the entry points. The ticket says nothing about packaging, so the PRD either states it in section 1 or names it
in a `NEEDS CLARIFICATION` marker. Silence is the failure the 0.5 acceptance run hit: the first
build stopped on the gap rule.
