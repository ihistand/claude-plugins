"""prd_gates.py list and answer (0.8.1): every pending human decision of a PRD, in one shape, and one reply passed to its owner."""
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import confirm, deploy, model
from .model import Prd

REVIEW_FILE = ".prd-review.json"
PENDING = "; pending"
MAX_EVIDENCE = 20
KIND_ORDER = ("approval", "error-class", "deploy-step", "adoption", "signoff")
# an adoption gate's `choices` is the decisions its open items allow (this order), then `done`
DECISION_ORDER = ("confirm", "correct", "bug", "intended", "fix", "answer", "ask")


@dataclass
class Gate:
    id: str
    kind: str
    title: str
    question: str
    evidence: list[str]
    choices: list[str]
    source: str
    path: str | None = None
    items: list[str] | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _git(cwd: Path, *args: str) -> str:
    run = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return run.stdout if run.returncode == 0 else ""


def branch_of(root: Path) -> str:
    """The checked-out branch of the worktree holding `root`; `HEAD` when detached."""
    return _git(root, "branch", "--show-current").strip() or "HEAD"


def _last_row(prd: Prd):
    from .change import _table_of

    text = prd.docs.get("prd.md", "")
    table = _table_of(text, 14)
    return table.rows[-1] if table and table.rows else None


def approval_gate(prd_root: Path, branch: str, path: str | None = None) -> Gate | None:
    """Pending when a ready verdict's digest equals the PRD's and the last §14 row ends `; pending`."""
    from .change import digest

    verdict_path = Path(prd_root) / REVIEW_FILE
    try:
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(verdict, dict) or verdict.get("ready") is not True or verdict.get("digest") != digest(prd_root):
        return None
    prd = model.load(Path(prd_root))
    last = _last_row(prd)
    if last is None or len(last.cells) < 3 or not last.cells[2].endswith(PENDING):
        return None
    slug, version = prd.frontmatter.get("prd", Path(prd_root).name), last.cells[0]
    record = (verdict.get("dry_run") or {}).get("record")
    evidence = [str(x) for x in (record,) if x] + [f"touches: {', '.join(map(str, verdict['touches']))}"] * bool(verdict.get("touches"))
    restate = str(verdict.get("restate") or last.cells[2][:-len(PENDING)])
    return Gate(f"approval:{branch}", "approval", f"Approve {slug} {version}", f"{restate} Approve it, or send it back with changes?",
                evidence[:MAX_EVIDENCE], ["approve", "changes"], REVIEW_FILE, path=path)


def _approval(prd: Prd, repo_root: Path, worktrees: bool) -> list[Gate]:
    here = repo_root.resolve()
    found = []
    mine = approval_gate(prd.root, branch_of(prd.root), str(here) if worktrees else None)
    if mine:
        found.append(mine)
    if not worktrees:
        return found
    rel = prd.root.resolve().relative_to(here)
    paths, current = [], {}
    for line in _git(repo_root, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not line:
            if current.get("worktree"):
                paths.append(current)
            current = {}
        else:
            key, _, value = line.partition(" ")
            current[key] = value
    for wt in paths:
        root = Path(wt["worktree"]).resolve()
        if root == here or "bare" in wt:
            continue
        branch = wt.get("branch", "").removeprefix("refs/heads/") or "HEAD"
        try:
            gate = approval_gate(root / rel, branch, str(root))
        except Exception:
            continue
        if gate:
            found.append(gate)
    return found


def _error_class(prd: Prd) -> list[Gate]:
    return [Gate(f"error-class:{e.id}", "error-class", e.title, f"Proposed class: {e.classification}. Confirm it, or correct it to another class.",
                 [str(x) for x in e.evidence[:MAX_EVIDENCE]], ["confirm", "correct"], f"errors.md:{e.line}")
            for e in prd.errors_ledger.values() if e.state == "proposed"]


def _deploy_step(prd: Prd, repo_root: Path) -> list[Gate]:
    try:
        run_ids = sorted(p.stem for p in deploy.log_dir(repo_root).glob("*.jsonl"))
        mine = deploy.prd_rel(prd, repo_root)
    except Exception:
        return []
    steps = {s.number: s for s in prd.operations.steps}
    out = []
    for run_id in run_ids:
        try:
            recs = deploy.read_log(repo_root, run_id)
        except Exception:
            continue
        if not recs or recs[0].get("kind") != "header" or recs[0].get("prd") != mine:
            continue
        last = deploy._last_step(recs)
        if not last or last.get("result") != "human" or deploy._confirmed(recs, last["step"]):
            continue
        n, step = last["step"], steps.get(last["step"])
        do = step.labels.get("Do", ("", 0))[0] if step else ""
        check = step.labels.get("Check", ("", 0))[0] if step else ""
        title = f"Run {run_id} step {n}: {step.title}" if step else f"Run {run_id} step {n}"
        question = f"{step.title if step else 'Human step'}. {do}".strip()
        out.append(Gate(f"deploy-step:{run_id}:{n}", "deploy-step", title, question,
                        [f"Check: {check}"] if check else [], ["confirm"], "operations.md"))
    return out


def _adoption(prd: Prd, repo_root: Path) -> list[Gate]:
    out = []
    for row in prd.adoption or []:
        if row.state != "extracted":
            continue
        path = confirm.answers_path(repo_root, row.area)
        try:
            answers = confirm.load_answers(path)
        except confirm.Refused:
            answers = {}
        if not path.is_file() or answers.get("done") is True:
            continue
        try:
            items = confirm.build_items(prd, row.area)
        except confirm.Refused:
            items = []
        open_ids = set(confirm.open_ids(items, answers))
        kinds = {i.kind for i in items if i.id in open_ids}
        allowed = {d for k in kinds for d in confirm.ALLOWED[k]}
        choices = [d for d in DECISION_ORDER if d in allowed] + ["done"]
        out.append(Gate(f"adoption:{row.area}", "adoption", f"Adopt area {row.area}",
                        f"{len(open_ids)} of {len(items)} items of area {row.area} are open. Answer each, then mark the area done.",
                        [], choices, path.name, items=[i.id for i in items if i.id in open_ids]))
    return out


def _signoff(prd: Prd) -> list[Gate]:
    done = {r.cells[0] for r in prd.testing.signoffs if len(r.cells) > 3 and r.cells[3].strip()}
    out = []
    for tc in prd.test_cases:
        owner = tc.data.get("signoff")
        if tc.data.get("level") != "acceptance" or not owner or tc.id in done:
            continue
        steps = [str(s) for s in (tc.data.get("steps") or [])][:MAX_EVIDENCE]
        out.append(Gate(f"signoff:{tc.id}", "signoff", f"Sign off {tc.id}",
                        f"{owner} walks the steps of {tc.id} and reports the result: pass or fail.", steps, ["pass", "fail"], f"{tc.file}:{tc.line}"))
    return out


def list_gates(prd: Prd, repo_root: Path, worktrees: bool = False) -> list[Gate]:
    """Every pending gate, in the kind order of KIND_ORDER, then by id."""
    gates = (_approval(prd, Path(repo_root), worktrees) + _error_class(prd) + _deploy_step(prd, Path(repo_root))
             + _adoption(prd, Path(repo_root)) + _signoff(prd))
    return sorted(gates, key=lambda g: (KIND_ORDER.index(g.kind), g.id))


# --- answer: one reply for one gate, passed to the script that owns the decision ---

SCRIPTS = Path(__file__).resolve().parent.parent  # the scripts beside this package, so a vendored copy calls vendored scripts
REFUSED_CHANGED = "the gate changed; list again"


class Refused(Exception):
    """A refusal by `answer` itself: nothing ran and nothing was written."""


def _run(script: str, *argv: str) -> dict:
    """Call an owning script as `<this interpreter> <script> argv...`: an argv list, never a shell string."""
    run = subprocess.run([sys.executable, str(SCRIPTS / script), *argv], capture_output=True, text=True, encoding="utf-8",
                         env={**os.environ, "PYTHONUTF8": "1"})
    out = {"stdout": run.stdout.splitlines(), "exit": run.returncode}
    if run.stderr.strip():
        out["stderr"] = run.stderr.splitlines()
    return out


def _atomic_write(path: Path, text: str) -> None:
    """A temp file in the same folder, then os.replace."""
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _pick(gate: Gate, choice: str | None, default: str) -> str:
    choice = choice or default
    if choice not in gate.choices:
        raise Refused(f"{gate.id} offers {', '.join(gate.choices)}, not {choice}")
    return choice


def _answer_approval(prd: Prd, gate: Gate, reply: str, choice: str | None, **_) -> dict:
    choice = _pick(gate, choice, "approve")
    root = Path(prd.root)
    if choice == "changes":
        path = root / REVIEW_FILE
        verdict = json.loads(path.read_text(encoding="utf-8"))
        verdict["owner"] = {"choice": "changes", "reply": reply, "at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        verdict["ready"] = False
        verdict["blockers"] = [*(verdict.get("blockers") or []), f"owner: {reply}"]
        _atomic_write(path, json.dumps(verdict, ensure_ascii=False, indent=2) + "\n")
        return {"stdout": [f"recorded changes for {gate.id}"], "exit": 0}
    verdict = json.loads((root / REVIEW_FILE).read_text(encoding="utf-8"))
    record = (verdict.get("dry_run") or {}).get("record")
    if not record:
        raise Refused("the verdict holds no dry-run record")
    return _run("prd_change.py", "approve", str(root), f"--reply={reply}", f"--dry-run={record}")


def _answer_error_class(prd: Prd, gate: Gate, reply: str, choice: str | None, cls: str | None, **_) -> dict:
    choice = _pick(gate, choice, "confirm")
    if choice == "correct" and not cls:
        raise Refused("--choice correct needs --class")
    if choice == "confirm" and cls:
        raise Refused("--class goes with --choice correct")
    extra = [f"--class={cls}"] if choice == "correct" else []
    return _run("prd_error.py", "confirm", str(prd.root), gate.id.split(":", 1)[1], f"--reply={reply}", *extra)


def _answer_deploy_step(prd: Prd, gate: Gate, reply: str, choice: str | None, **_) -> dict:
    _pick(gate, choice, "confirm")
    run_id, step = gate.id.split(":", 1)[1].rsplit(":", 1)
    return _run("prd_deploy.py", "confirm", str(prd.root), "--run", run_id, "--step", step, f"--reply={reply}")


def _answer_adoption(prd: Prd, gate: Gate, reply: str, choice: str | None, item: str | None, correction: str | None, repo_root: Path, **_) -> dict:
    area = gate.id.split(":", 1)[1]
    if choice == "done":
        return _run("prd_confirm.py", "done", str(prd.root), area)
    if not item or not choice:
        raise Refused("an adoption answer needs --item with --choice, or --choice done")
    try:
        by_id = {i.id: i for i in confirm.build_items(prd, area)}
    except confirm.Refused as e:
        raise Refused(str(e)) from None
    if item not in by_id:
        raise Refused(f"unknown item {item!r}")
    allowed = confirm.ALLOWED[by_id[item].kind]
    if choice not in allowed:
        raise Refused(f"{item} cannot be answered {choice}; allowed: {', '.join(sorted(allowed))}")
    extra = [f"--correction={correction}"] if correction is not None else []
    return _run("prd_confirm.py", "answer", str(prd.root), area, item, "--decision", choice, f"--reply={reply}", *extra)


def _answer_signoff(prd: Prd, gate: Gate, reply: str, choice: str | None, result: str | None, **_) -> dict:
    """`--result` is required and is the sign-off; `--choice`, when given, must equal it."""
    if result is None:
        raise Refused("signoff needs --result pass|fail")
    if result not in ("pass", "fail"):
        raise Refused("--result must be pass or fail")
    if choice is not None and choice != result:
        raise Refused(f"--choice {choice} disagrees with --result {result}")
    tid = gate.id.split(":", 1)[1]
    case = next(tc for tc in prd.test_cases if tc.id == tid)
    row = f"| {tid} | {case.data.get('signoff')} | {datetime.date.today().isoformat()} | {result} |"
    path = Path(prd.root) / "testing.md"
    _atomic_write(path, _with_signoff_row(path.read_text(encoding="utf-8"), tid, row))
    return {"stdout": [row], "exit": 0}


def _with_signoff_row(text: str, tid: str, row: str) -> str:
    """Append `row` to the Sign-offs table, or fill the row that names `tid` and holds no result."""
    lines = text.split("\n")
    start = next((n for n, ln in enumerate(lines) if re.match(r"^#+\s*Sign-offs\s*$", ln)), None)
    if start is None:
        raise Refused("testing.md has no Sign-offs section")
    end = next((n for n in range(start + 1, len(lines)) if lines[n].startswith("#")), len(lines))
    table = [n for n in range(start + 1, end) if lines[n].startswith("|")]
    if not table:
        body = [lines[n] for n in range(start + 1, end) if lines[n].strip() not in ("", "None.", "None")]
        lines[start + 1:end] = ["", "| T-id | Owner | Date | Result |", "|---|---|---|---|", row, "", *body]
        return "\n".join(lines)
    for n in table:
        cells = [c.strip() for c in lines[n].strip().strip("|").split("|")]
        if cells[0] == tid and len(cells) > 3 and not cells[3]:
            lines[n] = row
            return "\n".join(lines)
    lines.insert(table[-1] + 1, row)
    return "\n".join(lines)


ANSWERERS = {"approval": _answer_approval, "error-class": _answer_error_class, "deploy-step": _answer_deploy_step,
             "adoption": _answer_adoption, "signoff": _answer_signoff}


def answer(prd: Prd, repo_root: Path, gate_id: str, reply: str, choice: str | None = None, cls: str | None = None,
           result: str | None = None, item: str | None = None, correction: str | None = None, question: str | None = None) -> dict:
    """Pass one reply for one gate to its owner: `{gate, result}`, `result` being the owner's `{stdout, exit}`. Raises Refused."""
    if not isinstance(reply, str) or not reply.strip():
        raise Refused("the reply is empty")
    gate = next((g for g in list_gates(prd, repo_root) if g.id == gate_id), None)
    if gate is None or (question is not None and gate.question != question):
        raise Refused(REFUSED_CHANGED)
    out = ANSWERERS[gate.kind](prd, gate, reply, choice=choice, cls=cls, result=result, item=item, correction=correction, repo_root=Path(repo_root))
    return {"gate": gate.id, "result": out}
