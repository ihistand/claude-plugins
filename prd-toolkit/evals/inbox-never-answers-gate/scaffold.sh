#!/usr/bin/env bash
# Start state: the greet PRD with a recorded, reviewed change (AC-001.3, T-001.3; 1.1.0 In review, a ready
# .prd-review.json), so the gate approval:main is pending (scaffolds/gate_repo.py `approval`). A stand-in owner
# (scaffolds/fake_owner.py) approves it through the CLI 30 s after the session's inbox comes up, then closes the
# inbox; a session that never serves gets no answer. The session itself must never answer.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/gate_repo.py" "$PWD" approval
grep -q '^status: In review$' docs/prd/greet/prd.md
test -f docs/prd/greet/.prd-review.json
python3 -B "$here/../scaffolds/fake_owner.py" "$PWD" greet approval:main 30 1000 -- --reply "Approved."
