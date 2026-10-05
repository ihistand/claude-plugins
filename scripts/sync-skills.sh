#!/usr/bin/env bash
#
# Sync canonical skills into the plugin copies in this marketplace. Plugins must
# ship a *copy* of each skill (a published plugin can't symlink to a path on your
# machine), so run this whenever a canonical skill changes — then commit + push
# this repo. That keeps the plugin copies from drifting out of sync.
#
# Each skill is mirrored as a whole directory (SKILL.md plus any scripts/ and
# references/) to <plugin>/skills/<skill>/SKILL.md. That is the only layout
# Claude Code loads; a flat skills/<skill>.md is silently ignored.
#
# Sources of truth (override with the environment variables):
#   CLAUDE_SKILLS_DIR    ~/projects-ivan/claude-skills          (ihistand/claude-skills)
#   SQLANVIL_SKILLS_DIR  ~/projects-ivan/sqlanvil/agent-skills/skills  (SQLAnvil/agent-skills)
#
# Usage:  ./scripts/sync-skills.sh
#
set -euo pipefail

CLAUDE_SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/projects-ivan/claude-skills}"
SQLANVIL_SKILLS="${SQLANVIL_SKILLS_DIR:-$HOME/projects-ivan/sqlanvil/agent-skills/skills}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# <skill-dir-name> <plugin-dir-name> <source-root>
SKILLS=(
  "sqlanvil-engineering-fundamentals sqlanvil-toolkit $SQLANVIL_SKILLS"
  "stl-generator stl-generator-toolkit $CLAUDE_SKILLS"
)

changed=0
missing=0
for entry in "${SKILLS[@]}"; do
  read -r skill plugin src_root <<<"$entry"
  src="$src_root/$skill"
  dst="$ROOT/$plugin/skills/$skill"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "MISSING:     $src/SKILL.md (moved?); skipped $plugin" >&2
    missing=1
    continue
  fi
  mkdir -p "$dst"
  if diff -rq -x __pycache__ "$src" "$dst" >/dev/null 2>&1; then
    echo "up to date:  $plugin/skills/$skill/"
  else
    rsync -a --delete --exclude __pycache__ "$src/" "$dst/"
    echo "SYNCED:      $plugin/skills/$skill/  <-  $src/"
    changed=1
  fi
done

echo
if [ "$changed" -eq 1 ]; then
  echo "Skill copies updated. Review 'git status', then commit and push to publish."
else
  echo "All plugin skill copies already match the canonical skills."
fi
if [ "$missing" -eq 1 ]; then
  echo "Some canonical skills were missing; their plugin copies were left as they are." >&2
  exit 1
fi
