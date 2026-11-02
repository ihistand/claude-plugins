---
type: regex
pattern: '## 1\. Metadata & stack(?=(?:(?!\n## 2\.)[\s\S])*?(?:pip install|uv sync|uv tool install|pipx install|uv pip install|install command))|NEEDS CLARIFICATION: [^\]]*(?:install)'
target: { source: file, path: docs/prd/hello/prd.md }
---

The PRD names the install command. The ticket says nothing about packaging, so the PRD either states it in section 1 or names it
in a `NEEDS CLARIFICATION` marker. Silence is the failure the 0.5 acceptance run hit: the first
build stopped on the gap rule.
