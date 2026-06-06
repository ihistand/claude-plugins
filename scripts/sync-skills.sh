#!/usr/bin/env bash
#
# Sync canonical skills from the claude-skills repo into the plugin copies in
# this marketplace. Plugins must ship a *copy* of each skill (a published plugin
# can't symlink to a path on your machine), so run this whenever a canonical
# skill changes — then commit + push this repo. That keeps the plugin copies
# from drifting out of sync with the source of truth.
#
# Source of truth: ~/projects/claude-skills (override with CLAUDE_SKILLS_DIR).
#
# Usage:  ./scripts/sync-skills.sh
#
set -euo pipefail

SKILLS_SRC="${CLAUDE_SKILLS_DIR:-$HOME/projects/claude-skills}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# <canonical-skill-dir-name> <plugin-dir-name>
SKILLS=(
  "dataform-engineering-fundamentals dataform-toolkit"
  "sqlanvil-engineering-fundamentals sqlanvil-toolkit"
)

changed=0
for entry in "${SKILLS[@]}"; do
  read -r skill plugin <<<"$entry"
  src="$SKILLS_SRC/$skill/SKILL.md"
  dst="$ROOT/$plugin/skills/$skill.md"
  if [ ! -f "$src" ]; then
    echo "ERROR: canonical skill not found: $src" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dst")"
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
    echo "up to date:  $plugin/skills/$skill.md"
  else
    cp "$src" "$dst"
    echo "SYNCED:      $plugin/skills/$skill.md  <-  $skill/SKILL.md"
    changed=1
  fi
done

if [ "$changed" -eq 1 ]; then
  echo
  echo "Skill copies updated. Review 'git status', then commit and push to publish."
else
  echo
  echo "All plugin skill copies already match the canonical skills."
fi
