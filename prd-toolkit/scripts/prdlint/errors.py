"""errors.md writes: each command replaces or inserts lines inside one entry and nothing else in the file moves."""
import re
from datetime import date
from pathlib import Path

from .deploy import LEDGER_PLACEHOLDER, Refused
from .model import CLASSES, ErrorEntry, Prd, _errors_ledger

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
