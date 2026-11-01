"""errors.md writes: each command replaces or inserts lines inside one entry and nothing else in the file moves."""
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from . import deploy, trace
from .buildcheck import _resolve, _show
from .deploy import LEDGER_PLACEHOLDER, Refused
from .markdown import tables
from .model import CLASSES, ErrorEntry, Prd, _errors_ledger, load

MAX_EVIDENCE = 20
ORDER = ("Detected", "Classification", "Confirmed", "Touches", "Evidence", "Diagnosis", "Resolution", "Recurrence of")
_FIELD = re.compile(r"^(" + "|".join(ORDER) + r"):")
_VERSION = re.compile(r"\d+\.\d+\.\d+")
_COMMIT = re.compile(r"[0-9a-f]{7,40}")
_TID = re.compile(r"T-\d{3}\.\d+")
_RUN = re.compile(r"[^\s,]+")


def _one(text: str) -> str:
    """Line breaks and runs of spaces collapse to single spaces."""
    return " ".join(text.split())


def _path(prd: Prd) -> Path:
    return prd.root / "errors.md"


def _read(prd: Prd) -> str:
    p = _path(prd)
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _entry(text: str, eid: str) -> ErrorEntry:
    e = _errors_ledger(text).get(eid)
    if e is None:
        raise Refused([f"{eid} is not an entry"])
    return e


def _set(text: str, eid: str, name: str, value: str) -> str:
    """Replace the entry's `name:` line, or insert it after the last earlier field in the canonical order."""
    e = _entry(text, eid)
    lines = text.split("\n")
    at = ORDER.index(name)
    last = e.line  # 1-based line to insert after; the heading when no earlier field exists
    n = e.line + 1
    while n <= e.end:
        m = _FIELD.match(lines[n - 1])
        if m:
            end = n
            if m.group(1) == "Evidence":
                while end < e.end and lines[end].startswith("  "):
                    end += 1
            if m.group(1) == name:
                lines[n - 1:end] = [f"{name}: {value}"]
                return "\n".join(lines)
            if ORDER.index(m.group(1)) < at:
                last = end
            n = end
        n += 1
    lines.insert(last, f"{name}: {value}")
    return "\n".join(lines)


def _write(prd: Prd, text: str) -> None:
    _path(prd).write_text(text, encoding="utf-8")


def _check_class(cls: str) -> None:
    if cls not in CLASSES or cls == "unclassified":
        raise ValueError(f"class must be one of {', '.join(c for c in CLASSES if c != 'unclassified')}; got {cls!r}")


def new(prd: Prd, title: str, source: str, touches: list[str], evidence: list[str], today: date) -> str:
    title, source = _one(title), _one(source)
    if not title or not source:
        raise ValueError("a title and a source are required")
    reasons = []
    known = {b.id for b in prd.blocks}
    unknown = [t for t in touches if t not in known]
    if unknown:
        reasons.append(f"Touches: {', '.join(unknown)} {'is' if len(unknown) == 1 else 'are'} not defined in the PRD")
    evidence = [ln.rstrip() for ln in evidence]
    while evidence and not evidence[-1]:
        evidence.pop()
    if len(evidence) > MAX_EVIDENCE:
        reasons.append(f"Evidence: is {len(evidence)} lines; at most {MAX_EVIDENCE}")
    if reasons:
        raise Refused(reasons)
    text = _read(prd)
    ledger = _errors_ledger(text)
    eid = "E-%03d" % (max((int(i[2:]) for i in ledger), default=0) + 1)
    block = [f"### {eid} {title}", f"Detected: {today.isoformat()}, {source}", "Classification: unclassified"]
    if touches:
        block.append("Touches: " + ", ".join(touches))
    if evidence:
        block.append("Evidence: " + evidence[0])
        block += ["  " + ln for ln in evidence[1:]]
    block += ["Diagnosis: -", "Resolution: -", "Recurrence of: -"]
    entry = "\n".join(block)
    lines = text.split("\n")
    if not ledger and LEDGER_PLACEHOLDER in (ln.strip() for ln in lines):
        out = "\n".join(entry if ln.strip() == LEDGER_PLACEHOLDER else ln for ln in lines)
    elif text.strip():
        out = text.rstrip("\n") + "\n\n" + entry + "\n"
    else:
        out = "# Error ledger\n\n" + entry + "\n"
    _write(prd, out)
    return eid


def propose(prd: Prd, eid: str, cls: str, diagnosis: str, recurrence: str | None) -> None:
    _check_class(cls)
    diagnosis = _one(diagnosis)
    if not diagnosis:
        raise ValueError("a diagnosis is required")
    text = _read(prd)
    e = _entry(text, eid)
    if e.state in ("confirmed", "resolved"):
        raise Refused([f"{eid} is {e.state}; its class is settled" if e.state == "confirmed" else f"{eid} is resolved"])
    if recurrence is not None and recurrence not in _errors_ledger(text):
        raise Refused([f"Recurrence of: {recurrence} is not an entry"])
    text = _set(text, eid, "Classification", cls)
    text = _set(text, eid, "Diagnosis", diagnosis)
    if recurrence is not None:
        text = _set(text, eid, "Recurrence of", recurrence)
    _write(prd, text)


def confirm(prd: Prd, eid: str, reply: str, today: date, cls: str | None = None) -> None:
    reply = _one(reply)
    if not reply:
        raise ValueError("the reply is empty")
    if cls is not None:
        _check_class(cls)
    text = _read(prd)
    e = _entry(text, eid)
    if e.state == "resolved":
        raise Refused([f"{eid} is resolved"])
    if e.state == "unclassified":
        raise Refused([f"{eid} is unclassified; propose a class first"])
    if e.state == "confirmed":
        raise Refused([f"{eid} is already confirmed"])
    if cls is not None:
        text = _set(text, eid, "Classification", cls)
    _write(prd, _set(text, eid, "Confirmed", f'{today.isoformat()}, "{reply}"'))


def resolve(prd: Prd, eid: str, *, t: str | None, level: str | None, version: str, commit: str | None,
            run: str | None, not_a_defect: str | None) -> None:
    if not_a_defect is not None:
        if any((t, level, commit, run)) or version:
            raise ValueError("--not-a-defect stands alone")
        why = _one(not_a_defect)
        if not why:
            raise ValueError("say why it is not a defect")
        value = f"not a defect: {why}"
    else:
        if not _VERSION.fullmatch(version or ""):
            raise ValueError(f"version must be X.Y.Z; got {version!r}")
        if t is not None and not _TID.fullmatch(t):
            raise ValueError(f"not a T-id: {t!r}")
        if run is not None:
            if commit is not None or not _RUN.fullmatch(run):
                raise ValueError("--run takes a run id and no commit")
            value = f"{t or '-'}, PRD {version}, run {run}"
        else:
            if not t or not level or not commit:
                raise ValueError("a fix needs a T-id, its level and a commit")
            if not _COMMIT.fullmatch(commit):
                raise ValueError(f"commit must be 7 to 40 lowercase hex digits; got {commit!r}")
            value = f"{t} [{level}], PRD {version}, fixed in {commit}"
    text = _read(prd)
    e = _entry(text, eid)
    if e.state == "resolved":
        raise Refused([f"{eid} is already resolved"])
    if e.state != "confirmed":
        raise Refused([f"{eid} is not confirmed"])
    _write(prd, _set(text, eid, "Resolution", value))


def entry_lines(prd: Prd, eid: str) -> list[str]:
    text = _read(prd)
    e = _entry(text, eid)
    out = text.split("\n")[e.line - 1:e.end]
    while out and not out[-1].strip():
        out.pop()
    return out


def summary(e: ErrorEntry) -> str:
    """`confirmed code bug`, or just `unclassified`: the state, then the class when it adds something."""
    cls = e.classification
    return e.state if cls in ("", e.state) else f"{e.state} {cls}"


def list_lines(prd: Prd, open_only: bool) -> list[str]:
    return [f"{e.id} {summary(e)} {', '.join(t for t, _ in e.touches) or '-'} {e.title}".rstrip()
            for e in _errors_ledger(_read(prd)).values() if e.open or not open_only]


_FIX = re.compile(r"(T-\d{3}\.\d+) \[[^\]\s][^\]]*\], PRD (\d+\.\d+\.\d+), fixed in ([0-9a-f]{7,40})")
_ENV = re.compile(r"(T-\d{3}\.\d+|-), PRD (\d+\.\d+\.\d+), run (\S+)")
_NOT_A_DEFECT = re.compile(r"not a defect: \S.*")
_RANGE = re.compile(r"^([^.\s][^\s]*?)\.\.([^.\s][^\s]*)$")
_STEP = re.compile(r"\bstep\s+(\d+)\b")
_TOKEN = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*")


def _ver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def _structure(prev: dict[str, ErrorEntry], cur: dict[str, ErrorEntry]) -> list[tuple[str, str]]:
    """What one write did to the ledger besides adding entries and filling in lines: (E-id, finding)."""
    out: list[tuple[str, str]] = []
    added = [e for i, e in cur.items() if i not in prev]
    for eid, e in prev.items():
        if eid not in cur:
            twin = next((a for a in added if a.title == e.title), None)
            out.append((eid, f"renumbered to {twin.id}" if twin else "deleted"))
    common = [i for i in cur if i in prev]
    before = {i: n for n, i in enumerate(prev)}
    for n, x in enumerate(common):
        later = next((y for y in common[n + 1:] if before[y] < before[x]), None)
        if later:
            out.append((x, f"moved before {later}"))
    for eid in common:
        a, b = prev[eid], cur[eid]
        if a.detected != b.detected:
            out.append((eid, "Detected: changed"))
        if a.confirmed_raw is not None:
            if a.classification != b.classification:
                out.append((eid, "Classification: changed after Confirmed:"))
            if a.confirmed_raw != b.confirmed_raw:
                out.append((eid, "Confirmed: changed"))
    return out


def _resolution(prd: Prd, repo_root: Path, head: str, e: ErrorEntry, cited: dict, tagged: dict, versions: set[str]) -> list[str]:
    """Findings on a resolution added in the range, judged against the PRD at head."""
    text = e.resolution
    fix, env, nad = _FIX.fullmatch(text), _ENV.fullmatch(text), _NOT_A_DEFECT.fullmatch(text)
    if not (fix or env or nad):
        return ["resolution is not one of the three forms"]
    out: list[str] = []
    if nad:
        return out
    tid, version = (fix or env).group(1), (fix or env).group(2)
    if tid != "-":
        cases = {tc.id: tc for tc in prd.test_cases}
        if tid not in cases:
            out.append(f"{tid} has no test case")
        else:
            if tid not in cited:
                out.append(f"{tid} is cited by no test")
            if cases[tid].data.get("known-failing") == e.id or (tid, e.id) in tagged:
                out.append(f"{tid} is still known-failing on {e.id}")
    head_version = prd.frontmatter.get("version", "")
    if re.fullmatch(r"\d+\.\d+\.\d+", head_version) and _ver(version) > _ver(head_version):
        out.append(f"PRD {version} is above the PRD version {head_version}")
    elif version not in versions:
        out.append(f"PRD {version} has no changelog row")
    if fix:
        commit = fix.group(3)
        ok = subprocess.run(["git", "merge-base", "--is-ancestor", commit + "^{commit}", head], cwd=repo_root,
                            capture_output=True, timeout=60).returncode == 0
        if not ok:
            out.append(f"commit {commit} is not an ancestor of HEAD")
    else:
        out += _run_finished(prd, repo_root, e, env.group(3))
    return out


def _run_finished(prd: Prd, repo_root: Path, e: ErrorEntry, run_id: str) -> list[str]:
    """A `run R` resolution: R's log shows the environment of the entry's failed run finished. Not applicable when
    `Detected:` names no run."""
    step = _STEP.search(e.detected)
    if not step:
        return []
    named = next((t for t in _TOKEN.findall(e.detected)
                  if deploy.RUN_ID.fullmatch(t) and deploy.detected_names_failure(e.detected, t, step.group(1))
                  and deploy._log_path(repo_root, t).is_file()), None)
    if named is None:
        return []
    env = next((s.env for s in prd.operations.steps if s.number == int(step.group(1))), None)
    if not env:
        return []
    try:
        finished = deploy.finished_envs(deploy.read_log(repo_root, run_id), prd)
    except (OSError, ValueError):
        finished = []
    return [] if env in finished else [f"run {run_id} did not finish {env}"]


def _changelog_versions(prd: Prd) -> set[str]:
    for s in prd.sections:
        if s.title.strip().lower() == "changelog":
            ts = tables(s.body)
            return {r.cells[0].strip() for r in ts[0].rows} if ts else set()
    return set()


def check_findings(prd: Prd, repo_root: Path, rng: str) -> list[str]:
    """Findings for every change to errors.md in `base..head`, each `errors.md: E-nnn: <finding>`.

    BadRange for a bad range. Structure is judged write by write, the code-commit gate against errors.md at each
    commit, a resolution added in the range against the PRD at head."""
    m = _RANGE.match(rng)
    if not m or "..." in rng:
        raise trace.BadRange(f"bad range {rng}: expected <base>..<head>")
    base, head = _resolve(repo_root, rng, m.group(1)), _resolve(repo_root, rng, m.group(2))
    prefix = deploy.prd_rel(prd, repo_root)
    rel = "errors.md" if prefix == "." else f"{prefix}/errors.md"
    shas = deploy._git(repo_root, "rev-list", "--reverse", "--end-of-options", f"{base}..{head}").split()

    cache: dict[str, dict[str, ErrorEntry]] = {}

    def ledger_at(rev: str) -> dict[str, ErrorEntry]:
        text = _show(repo_root, rev, rel)
        if text not in cache:
            cache[text] = _errors_ledger(text)
        return cache[text]

    out: list[tuple[str, str]] = []
    prev = ledger_at(base)
    for sha in shas:
        cur = ledger_at(sha)
        if cur is not prev:
            out += _structure(prev, cur)
        prev = cur

    is_code = trace.outside_prd(prd, repo_root)
    for sha in shas:
        files = [f for f in deploy._git(repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "--root", sha).split("\0") if f]
        if not any(is_code(f) for f in files):
            continue
        body = deploy._git(repo_root, "log", "-1", "--format=%B", sha)
        cited = [r.strip() for m_ in trace._REFS.finditer(body) for r in m_.group(1).split(",")]
        for eid in dict.fromkeys(r for r in cited if trace._ERR_ID.fullmatch(r)):
            e = ledger_at(sha).get(eid)
            if e is None or e.confirmed_raw is None:
                out.append((eid, f"commit {sha[:8]} changes code and cites {eid}, which was not confirmed at that commit"))

    start, end = ledger_at(base), ledger_at(head)
    new = [e for i, e in end.items() if not e.open and (i not in start or start[i].open)]
    if new:
        with tempfile.TemporaryDirectory(prefix="prd-error-check-") as tmp:
            try:
                h_prd = load(deploy._tree(repo_root, head, prefix, Path(tmp)))
            except Exception as ex:
                raise trace.BadRange(f"cannot load the PRD at {head[:7]}: {ex}") from None
            cited, tagged, versions = trace.citations(prd, repo_root), trace.tagged_citations(prd, repo_root), _changelog_versions(h_prd)
            for e in new:
                if e.confirmed_raw is None:
                    out.append((e.id, "resolved without Confirmed:"))
                out += [(e.id, f) for f in _resolution(h_prd, repo_root, head, e, cited, tagged, versions)]
    return list(dict.fromkeys(f"errors.md: {eid}: {f}" for eid, f in out))
