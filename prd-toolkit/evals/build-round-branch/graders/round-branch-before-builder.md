---
type: regex
pattern: '^(?:(?!"subagent_type":"(?:prd-toolkit:)?prd-builder")[\s\S])*"name":"Bash","input":\{"command":"git switch -c prd-round/'
target: trace
---

A main-session Bash call `git switch -c prd-round/<area>-<n>` comes before the first prd-builder dispatch in the
trace: the round branch is cut from the build branch before the builder runs.
