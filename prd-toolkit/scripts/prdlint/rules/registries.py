"""Registry rules (registries, runbook-actors) and the skill-installed lookup."""
import json
import os
import re
import shlex
import shutil
from collections.abc import Iterator
from pathlib import Path

from ..findings import Finding
from ..markdown import sections, tables
from ..model import Prd, repo_root
from ..registry import rule

STANDARDS_DECISIONS = {"enforced", "declined", "proposed"}
SKILLS_DECISIONS = {"required", "recommended", "declined", "proposed"}


def installed_skill(skill: str, repo_root: Path) -> bool:
    """`plugin:skill` is installed when a `plugin@...` key is in the plugins file; a bare skill when its SKILL.md exists."""
    if ":" in skill:
        plugin = skill.split(":", 1)[0]
        path = Path(os.environ.get("PRD_PLUGINS_FILE") or Path.home() / ".claude/plugins/installed_plugins.json")
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            return False
        plugins = data.get("plugins", data) if isinstance(data, dict) else {}
        return isinstance(plugins, dict) and any(str(k).startswith(plugin + "@") for k in plugins)
    return any((base / ".claude/skills" / skill / "SKILL.md").is_file() for base in (Path.home(), repo_root))


def _registry_rows(prd: Prd, number: int) -> Iterator:
    sec = next((s for s in prd.sections if s.number == number), None)
    for t in tables(sec.body) if sec else []:
        yield from t.rows


def _command(cell: str) -> str | None:
    """First token of the first backticked span."""
    m = re.search(r"`([^`]*)`", cell)
    if not m:
        return None
    try:
        tokens = shlex.split(m.group(1))
    except ValueError:
        tokens = m.group(1).split()
    return tokens[0] if tokens else None


@rule("registries")
def registries(prd: Prd) -> Iterator[Finding]:
    approved = prd.frontmatter.get("status", "").strip() == "Approved"
    for r in _registry_rows(prd, 5):
        cells = [c.strip() for c in r.cells] + [""] * 5
        decision = cells[4].strip("`").strip()
        if decision not in STANDARDS_DECISIONS:
            yield Finding("prd.md", r.line, "registries", f"standards Decision '{decision}' is not one of enforced, declined, proposed")
            continue
        if decision == "proposed" and approved:
            yield Finding("prd.md", r.line, "registries", "standards row is still 'proposed' but the PRD is Approved")
        if decision == "enforced":
            cmd = _command(cells[1])
            if cmd is None or shutil.which(cmd) is None:
                yield Finding("prd.md", r.line, "registries", f"enforced linter command '{cmd or cells[1]}' is not on PATH")
    root = None
    for r in _registry_rows(prd, 6):
        cells = [c.strip() for c in r.cells] + [""] * 3
        skill, decision = cells[1].strip("`").strip(), cells[2].strip("`").strip()
        if decision not in SKILLS_DECISIONS:
            yield Finding("prd.md", r.line, "registries", f"skills Decision '{decision}' is not one of required, recommended, declined, proposed")
            continue
        if decision == "proposed" and approved:
            yield Finding("prd.md", r.line, "registries", "skills row is still 'proposed' but the PRD is Approved")
        if decision == "required":
            root = root or repo_root(prd.root)
            if not installed_skill(skill, root):
                yield Finding("prd.md", r.line, "registries", f"required skill '{skill}' is not installed")


_STEP = re.compile(r"^\s*\d+[.)]\s")
_ACTOR = re.compile(r"\(actor:\s*(agent|human)\)")


@rule("runbook-actors")
def runbook_actors(prd: Prd) -> Iterator[Finding]:
    text = prd.docs.get("operations.md")
    if text is None:
        return
    sec = next((s for s in sections(text) if s.title.strip().lower() == "runbook"), None)
    for n, line in sec.body if sec else []:
        if _STEP.match(line) and not _ACTOR.search(line):
            yield Finding("operations.md", n, "runbook-actors", "runbook step has no (actor: agent) or (actor: human)")
