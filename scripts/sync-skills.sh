#!/usr/bin/env bash
#
# Sync canonical skills from the claude-skills repo into the plugin copies in
# this marketplace. Plugins must ship a *copy* of each skill (a published plugin
# can't symlink to a path on your machine), so run this whenever a canonical
# skill changes — then commit + push this repo. That keeps the plugin copies
# from drifting out of sync with the source of truth.
#
# Source of truth: ~/projects-ivan/claude-skills (override with CLAUDE_SKILLS_DIR).
#
# Two layouts:
#   file  copies <skill>/SKILL.md to <plugin>/skills/<skill>.md (legacy flat file)
#   dir   mirrors the whole <skill>/ directory (SKILL.md plus scripts/ and
#         references/) to <plugin>/skills/<skill>/, the layout Claude Code loads
#
# Usage:  ./scripts/sync-skills.sh
#
set -euo pipefail

SKILLS_SRC="${CLAUDE_SKILLS_DIR:-$HOME/projects-ivan/claude-skills}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# <canonical-skill-dir-name> <plugin-dir-name> <file|dir>
SKILLS=(
  "sqlanvil-engineering-fundamentals sqlanvil-toolkit file"
  "stl-generator stl-generator-toolkit dir"
)

changed=0
missing=0
for entry in "${SKILLS[@]}"; do
  read -r skill plugin layout <<<"$entry"
  src="$SKILLS_SRC/$skill/SKILL.md"
  if [ ! -f "$src" ]; then
    echo "MISSING:     $skill/SKILL.md not in $SKILLS_SRC (moved?); skipped $plugin" >&2
    missing=1
    continue
  fi
  if [ "$layout" = "dir" ]; then
    dst_dir="$ROOT/$plugin/skills/$skill"
    mkdir -p "$dst_dir"
    if diff -rq -x __pycache__ "$SKILLS_SRC/$skill" "$dst_dir" >/dev/null 2>&1; then
      echo "up to date:  $plugin/skills/$skill/"
    else
      rsync -a --delete --exclude __pycache__ "$SKILLS_SRC/$skill/" "$dst_dir/"
      echo "SYNCED:      $plugin/skills/$skill/  <-  $skill/"
      changed=1
    fi
    continue
  fi
  dst="$ROOT/$plugin/skills/$skill.md"
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
if [ "$missing" -eq 1 ]; then
  echo "Some canonical skills were missing; their plugin copies were left as they are." >&2
  exit 1
fi
