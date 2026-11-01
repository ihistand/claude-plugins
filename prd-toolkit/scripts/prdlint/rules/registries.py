"""Registry rules (registries, runbook-actors) and the skill-installed lookup."""
import json
import os
import re
import shlex
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ..findings import Finding
from ..markdown import sections, tables
from ..model import Prd, repo_root
from ..registry import rule

STANDARDS_DECISIONS = {"enforced", "declined", "proposed"}
SKILLS_DECISIONS = {"required", "recommended", "declined", "proposed"}


def installed_skill(skill: str, repo_root: Path) -> bool:
    """A bare skill is installed when its SKILL.md exists under ~/.claude/skills or <repo>/.claude/skills.

    `plugin:skill` needs a `plugin@...` key in the plugins file. When an install of that plugin records an
    `installPath`, `<installPath>/skills/<skill>/SKILL.md` must also exist; without one, plugin presence is enough."""
    if ":" in skill:
        plugin, name = skill.split(":", 1)
        path = Path(os.environ.get("PRD_PLUGINS_FILE") or Path.home() / ".claude/plugins/installed_plugins.json")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        plugins = data.get("plugins", data) if isinstance(data, dict) else {}
        if not isinstance(plugins, dict):
            return False
        entries = [v for k, v in plugins.items() if str(k).startswith(plugin + "@")]
        if not entries:
            return False
        installs = [i for v in entries for i in (v if isinstance(v, list) else [v])]
        paths = [i["installPath"] for i in installs if isinstance(i, dict) and isinstance(i.get("installPath"), str)]
        return not paths or any((Path(p) / "skills" / name / "SKILL.md").is_file() for p in paths)
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


@dataclass(frozen=True)
class StandardsRow:
    glob: str
    command: str
    decision: str
    line: int


def standards_rows(prd: Prd) -> list[StandardsRow]:
    """The §5 rows: glob without backticks, the whole first backticked span as the command, the Decision cell."""
    rows = []
    for r in _registry_rows(prd, 5):
        cells = [c.strip() for c in r.cells] + [""] * 5
        m = re.search(r"`([^`]*)`", cells[1])
        rows.append(StandardsRow(cells[0].replace("`", "").strip(), m.group(1).strip() if m else "",
                                 cells[4].strip("`").strip(), r.line))
    return rows


@rule("registries")
def registries(prd: Prd) -> Iterator[Finding]:
    approved = prd.frontmatter.get("status", "").strip() == "Approved"
    ci = os.environ.get("PRD_LINT_CI") == "1"  # prd_lint.py --ci: skip the checks that depend on the machine
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
            if cmd is None:  # no command at all is a finding anywhere, CI included
                yield Finding("prd.md", r.line, "registries", f"enforced standards row has no linter command ('{cells[1]}'); put it in backticks")
            elif not ci and shutil.which(cmd) is None:  # --ci skips only the on-PATH lookup
                yield Finding("prd.md", r.line, "registries", f"enforced linter command '{cmd}' is not on PATH")
    root = None
    for r in _registry_rows(prd, 6):
        cells = [c.strip() for c in r.cells] + [""] * 3
        skill, decision = cells[1].strip("`").strip(), cells[2].strip("`").strip()
        if decision not in SKILLS_DECISIONS:
            yield Finding("prd.md", r.line, "registries", f"skills Decision '{decision}' is not one of required, recommended, declined, proposed")
            continue
        if decision == "proposed" and approved:
            yield Finding("prd.md", r.line, "registries", "skills row is still 'proposed' but the PRD is Approved")
        if decision == "required" and not ci:
            root = root or repo_root(prd.root)
            if not installed_skill(skill, root):
                yield Finding("prd.md", r.line, "registries", f"required skill '{skill}' is not installed; if it is built into Claude Code, mark the row 'recommended'")


MIGRATION_HINT = " (prd-toolkit 0.5 runbook format)"
_RUN_SHAPE = "step {n}: {label} must be one backticked command or tests <level>[, <level>]"


@rule("runbook-steps")
def runbook_steps(prd: Prd) -> Iterator[Finding]:
    text = prd.docs.get("operations.md")
    if text is None:
        return
    ops = prd.operations
    old_format = bool(ops.steps) and not any(s.env is not None for s in ops.steps) and "(env:" not in text
    first = True

    def out(line: int, msg: str) -> Finding:
        nonlocal first
        msg += MIGRATION_HINT if first and old_format else ""
        first = False
        return Finding("operations.md", line, "runbook-steps", msg)

    def marked(label: str, s) -> bool:  # an unfilled [NEEDS CLARIFICATION: ...] value is the markers-open rule's business
        return "[NEEDS CLARIFICATION:" in s.labels[label][0]

    expected = 1
    for s in ops.steps:
        n = s.number
        if s.number != expected:
            yield out(s.line, f"step {n}: expected step {expected}")
        expected = s.number + 1
        if s.actor is None:
            yield out(s.line, f"step {n}: the step line needs (actor: agent|human) (env: <environment>)")
            continue
        labels = s.labels
        if s.actor == "human":
            bad = [k for k in ("Run", "Rollback") if k in labels]
            if bad:
                yield out(labels[bad[0]][1], f"step {n}: a human step takes Do: and Check:, not {' or '.join(k + ':' for k in bad)}")
            elif "Do" not in labels or "Check" not in labels:
                yield out(s.line, f"step {n}: a human step needs Do: and Check:")
            continue
        if "Do" in labels:
            yield out(labels["Do"][1], f"step {n}: an agent step takes Run:, Check: and Rollback:, not Do:")
        if "Run" not in labels:
            yield out(s.line, f"step {n}: an agent step needs Run:")
        elif s.run is None and s.tests is None and not marked("Run", s):
            yield out(labels["Run"][1], _RUN_SHAPE.format(n=n, label="Run:") + f"; got '{labels['Run'][0]}'")
        if s.tests is not None:
            if "Check" in labels:
                yield out(labels["Check"][1], f"step {n}: a tests step has no Check:")
            continue
        if "Check" not in labels:
            yield out(s.line, f"step {n}: an agent step needs Check:")
        elif s.check is None and not marked("Check", s):
            yield out(labels["Check"][1], f"step {n}: Check: must be one backticked command, optionally followed by prints `<text>`; got '{labels['Check'][0]}'")
        if "Rollback" in labels and s.rollback is None and not marked("Rollback", s):
            yield out(labels["Rollback"][1], f"step {n}: Rollback: must be one backticked command; got '{labels['Rollback'][0]}'")
