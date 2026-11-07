---
type: regex
pattern: '^status: Approved$[\s\S]*^\| 1\.1\.0 \| [^|\n]* \| greet with no name greets the World; no dry run \(unit only\) \|'
flags: m
target: { source: file, path: docs/prd/greet/prd.md }
---

The change is approved at 1.1.0, by the stand-in owner's answer: it comes only while the session's `wait` runs
(fake_owner.py answers once the session waits on the gate), and `no-approve` and `no-gates-answer` keep the session
from writing it. A session that answered nothing and waited on nothing leaves `In review` and `pending`.
