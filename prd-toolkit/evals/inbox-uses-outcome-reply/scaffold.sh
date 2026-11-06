#!/usr/bin/env bash
# Start state: the greet PRD (1.0.0, every requirement verified) with a planted code bug and E-001 recorded and
# proposed as a `code bug`, both committed (scaffolds/gate_repo.py `proposed`), so error-class:E-001 is pending. A
# stand-in owner (scaffolds/fake_owner.py) corrects the class to `spec gap` through the CLI 30 s after the session's
# inbox comes up, then closes the inbox. The session goes on from that outcome.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/gate_repo.py" "$PWD" proposed
grep -q '^Classification: code bug$' docs/prd/greet/errors.md
test -z "$(git status --porcelain --untracked-files=no)"
python3 -B "$here/../scaffolds/fake_owner.py" "$PWD" greet error-class:E-001 30 1000 -- \
  --choice correct --class "spec gap" --reply "It is a spec gap: the PRD never says whether settings keys are case-sensitive."
