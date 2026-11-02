---
type: regex
pattern: '## 1\. Metadata(?=(?:(?!\n## 2\.)[\s\S])*?(?:hatchling|setuptools|flit|poetry|pdm|maturin|uv_build|build backend))(?=(?:(?!\n## 2\.)[\s\S])*?(?:pip install|uv sync|uv tool install|pipx install|uv pip install))|NEEDS CLARIFICATION: [^\]]*(?:packag|build backend|install command)'
target: { source: file, path: docs/prd/hello/prd.md }
---

The ticket says nothing about packaging, so the PRD either names a build backend and an install
command in section 1, or marks the gap with a `NEEDS CLARIFICATION` marker that mentions packaging,
the build backend or the install command. Silence on both is the failure the 0.5 acceptance run hit:
the first build stopped on the gap rule.
