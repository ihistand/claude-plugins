---
type: tool_used
tool: Agent
input_match: '"isolation"\s*:'
min: 0
max: 0
---

No Agent call passes `isolation`: the Agent tool's worktree is cut from the main checkout's HEAD, not from the build
branch. An attempt that the tool refuses counts too: the call was made.
