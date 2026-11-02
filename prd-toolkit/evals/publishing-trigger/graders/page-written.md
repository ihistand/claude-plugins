---
type: file_exists
path: greet-prd-1.0.0.html
---

The page is at the default path, `./<project>-prd-<version>.html` in the repository root (R26: Claude Code
refuses writes under `.git/`, so R24's `<git-common-dir>` path rendered nothing). RED's U2 wrote
`dist/greet-prd.html` and U1 wrote nothing, so both fail.
