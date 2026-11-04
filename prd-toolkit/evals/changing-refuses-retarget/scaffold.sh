#!/usr/bin/env bash
# Start state: D5's: scaffolds/doc_repo.py state `built` (FR-010 verified, docs/guide/install.md written), plus
# a `demo` pack vendored in .prd-toolkit/packs/demo/ (a custom type `deck`, target kind `slides`), so the pack
# the prompt names resolves and lists (the vendored prd_lint.py --list-packs lists .prd-toolkit/packs/, `demo` as
# `source not recorded`, since it is copied by hand; the skill lists from the plugin and counts a vendored pack) and the
# only reason to refuse is the built area. D5 used an installed plugin through PRD_PLUGINS_FILE instead; an
# eval run cannot set the session's environment.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -B "$here/../scaffolds/doc_repo.py" "$PWD" built
mkdir -p .prd-toolkit/packs/demo
cat > .prd-toolkit/packs/demo/pack.yaml <<'YAML'
pack: demo
version: 1.0.0
toolkit: ">=0.7.2,<0.9"
description: "Slide decks written as one Markdown file per deck."
contract-types:
  - {type: deck, files: contracts/deck.yaml, validator: "python3 ${PACK}/validate_deck.py"}
target-kinds: {slides: deck}
vocabulary: [slide, deck]
YAML
printf 'import sys\nsys.exit(0)\n' > .prd-toolkit/packs/demo/validate_deck.py
git add .prd-toolkit/packs/demo
git -c user.name="Legacy Dev" -c user.email=legacy@example.com -c commit.gpgsign=false \
  commit -qm "Vendor the demo pack" -m "Refs: none (no behaviour change)"
grep -q "^Status: verified (since 1.0.0)$" docs/prd/greet/features/guide.md
packs="$(uv run --quiet --script .prd-toolkit/prd_lint.py --list-packs)"
grep -q "^demo 1.0.0 " <<<"$packs"
uv run --quiet --script .prd-toolkit/prd_lint.py docs/prd/greet
test -z "$(git status --porcelain)"
