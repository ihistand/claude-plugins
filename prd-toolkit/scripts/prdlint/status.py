"""The status report: where every requirement of a PRD stands. Read-only and deterministic."""
import json
from dataclasses import asdict, dataclass
from itertools import groupby
from pathlib import Path

from . import deploy, trace
from .model import Prd, gate_of

PARTS = ("Header", "Requirements", "Adoption map", "Not built", "Not verified", "Open errors", "Deployed", "Matrix")


@dataclass(frozen=True)
class StatusItem:
    part: str
    id: str | None
    text: str


def _titles(prd: Prd) -> dict[str, str]:
    """errors.md entry id -> the title on its heading line."""
    lines = prd.docs.get("errors.md", "").split("\n")
    out = {}
    for e in prd.errors_ledger.values():
        words = lines[e.line - 1].split(None, 2)
        out[e.id] = words[2].strip() if len(words) > 2 else ""
    return out


def _requirements(prd: Prd) -> list[StatusItem]:
    counts: dict[str, dict[str, int]] = {}
    for b in prd.blocks:
        by = counts.setdefault(trace.area(b.file), {})
        status = b.status or "-"
        by[status] = by.get(status, 0) + 1
    order = sorted(counts, key=lambda a: (a == "nfr", list(counts).index(a)))
    return [StatusItem("Requirements", None, f"{a}: " + ", ".join(f"{s} {n}" for s, n in sorted(counts[a].items())))
            for a in order] or [StatusItem("Requirements", None, "None.")]


def _adoption(prd: Prd) -> list[StatusItem]:
    if prd.adoption is None:
        return [StatusItem("Adoption map", None, "Not applicable: new project")]
    rows = [StatusItem("Adoption map", r.area, f"{r.area} | {r.state} | {', '.join(r.boundary) or '-'}") for r in prd.adoption]
    return rows or [StatusItem("Adoption map", None, "None.")]


def _by_status(prd: Prd, part: str, status: str) -> list[StatusItem]:
    rows = [StatusItem(part, b.id, f"{b.id} {b.title} ({b.file})") for b in prd.blocks if b.status == status]
    return rows or [StatusItem(part, None, "None.")]


def _open_errors(prd: Prd) -> list[StatusItem]:
    titles = _titles(prd)
    rows = [StatusItem("Open errors", e.id, f"{e.id} {titles[e.id]}; Touches: " + (", ".join(t for t, _ in e.touches) or "-"))
            for e in prd.errors_ledger.values() if e.open]
    return rows or [StatusItem("Open errors", None, "None.")]


def _stopped(prd: Prd, repo_root: Path, env: str, after: str | None) -> str | None:
    """`run <id> stopped (<state>) at step <N>` for the newest usable log of this PRD that touches `env` and did not finish it."""
    try:
        run_ids = sorted((p.stem for p in deploy.log_dir(repo_root).glob("*.jsonl")), reverse=True)
        mine = deploy.prd_rel(prd, repo_root)
    except Exception:
        return None
    for run_id in run_ids:
        if after and run_id <= after:
            break
        try:
            log = deploy.read_log(repo_root, run_id)
            if not log or log[0].get("kind") != "header" or log[0].get("prd") != mine:
                continue  # another PRD's run, or a log too old to name its PRD
            touched = [r for r in log if r.get("kind") in ("start", "step") and r.get("env") == env]
            if not touched:
                continue
            if env in deploy.finished_envs(log, prd):
                return None
            last = touched[-1]
            state = "unfinished" if last["kind"] == "start" else {"human": "human", "fail": "failed"}.get(last.get("result"), "unfinished")
            return f"run {run_id} stopped ({state}) at step {last['step']}"
        except Exception:
            continue
    return None


def _deployed(prd: Prd, repo_root: Path) -> list[StatusItem]:
    ops = prd.operations
    rows = {r.env: r for r in ops.deployed}
    names = list(ops.environments) + [e for e in rows if e not in ops.environments]
    out = []
    for env in names:
        row = rows.get(env)
        if row:
            out.append(StatusItem("Deployed", env, f"{env}: {row.version} at {row.commit}, {row.date}"))
        stopped = _stopped(prd, repo_root, env, row.run if row else None)
        if stopped:
            out.append(StatusItem("Deployed", env, f"{env}: {stopped}"))
    return out or [StatusItem("Deployed", None, "None.")]


def _matrix(prd: Prd, repo_root: Path) -> list[StatusItem]:
    cited = trace.citations(prd, repo_root)
    rows = []
    for b in prd.blocks:
        cells = [f"{t} {level} {gate_of(prd, level) or '-'} {'cited' if t in cited else 'missing'}" for t, level, _ in b.tests]
        rows.append(StatusItem("Matrix", b.id, f"{b.id}: " + ("; ".join(cells) or "no tests")))
    return rows or [StatusItem("Matrix", None, "None.")]


def build_status(prd: Prd, repo_root: Path, display: str = "") -> list[StatusItem]:
    header = StatusItem("Header", None, f"PRD: {display or prd.root.as_posix()}\n"
                        f"version {prd.frontmatter.get('version', '-')}\nstatus {prd.frontmatter.get('status', '-')}")
    return ([header] + _requirements(prd) + _adoption(prd) + _by_status(prd, "Not built", "approved")
            + _by_status(prd, "Not verified", "built") + _open_errors(prd) + _deployed(prd, repo_root) + _matrix(prd, repo_root))


def render_text(items: list[StatusItem]) -> str:
    return "\n".join(f"## {part}\n\n" + "\n".join(i.text for i in group) + "\n"
                     for part, group in groupby(items, key=lambda i: i.part))


def render_json(items: list[StatusItem]) -> str:
    return json.dumps([asdict(i) for i in items], indent=2, sort_keys=True, ensure_ascii=False) + "\n"
