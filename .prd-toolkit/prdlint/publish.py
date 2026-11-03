"""Render a PRD folder as one self-contained HTML page (Business and Technical tabs)."""
import html
import re
import subprocess
from datetime import date
from pathlib import Path
from string import Template

from . import languages, status, trace
from .context import _section
from .deps import require
from .markdown import sections
from .model import Prd, ReqBlock, production_envs
from .rules.contracts import event_names, operation_ids, schema_tables

markdown_it = require("markdown_it", "markdown-it-py")

TEMPLATE = Path(__file__).resolve().parent.parent.parent / "templates/publish/page.html"
MAX_SUMMARY = 600
NO_COMMIT = "no commit"
_MD = markdown_it.MarkdownIt("commonmark", {"html": False}).enable("table").disable("image")
_MD.validateLink = lambda url: url.strip().lower().startswith(("#", "http://", "https://", "mailto:"))  # no data: or relative targets
_ID = re.compile(r"^([A-Z]+)-(\d+)$")


_LABELS: dict[str, str] = {}


def L(key: str, **fmt) -> str:
    """A chrome label in the PRD's language; a key its table lacks falls back to `en`."""
    text = _LABELS.get(key)
    if text is None:
        text = languages.load("en").labels[key]
    return text.format(**fmt) if fmt else text


def _use_language(prd: Prd) -> None:
    _LABELS.clear()
    _LABELS.update(languages.load("en").labels)
    table = languages.for_prd(prd)
    if table is not None:
        _LABELS.update(table.labels)


class Refused(Exception):
    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _e(text) -> str:
    return html.escape(str(text), quote=True)


def _md(text: str) -> str:
    return _MD.render(text)


def _inline(text: str) -> str:
    return _MD.renderInline(text)


def _none() -> str:
    return f'<p class="none">{_e(L("none"))}</p>'


def _table(header: list[str], rows: list[list[str]]) -> str:
    """A table of already-escaped cells."""
    if not rows:
        return _none()
    head = "".join(f"<th>{h}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _section_md(prd: Prd, number: int) -> str:
    s = _section(prd, number)
    text = "\n".join(t for _, t in s.body).strip() if s else ""
    return _md(text) if text else _none()


def _doc_section(prd: Prd, doc: str, title: str):
    return next((s for s in sections(prd.docs.get(doc, "")) if s.title.strip().lower() == title.lower()), None)


def _doc_section_md(prd: Prd, doc: str, title: str) -> str:
    s = _doc_section(prd, doc, title)
    text = "\n".join(t for _, t in s.body).strip() if s else ""
    return _md(text) if text else _none()


def _doc_md(prd: Prd, doc: str) -> str:
    """The body of a whole document (its tables), under the page's own heading rather than the document's title."""
    lines = prd.docs.get(doc, "").split("\n")
    body = "\n".join(lines[1:] if lines and lines[0].startswith("# ") else lines).strip()
    return _md(body) if body else _none()


# ---- summaries -------------------------------------------------------------------------------

def _areas(prd: Prd) -> dict[str, list[ReqBlock]]:
    out: dict[str, list[ReqBlock]] = {}
    for b in prd.blocks:
        out.setdefault(trace.area(b.file), []).append(b)
    return out


def summary_problems(prd: Prd, summaries: dict) -> list[str]:
    """Why a summaries document cannot be published; [] when it can."""
    if not isinstance(summaries, dict) or not isinstance(summaries.get("areas", {}), dict):
        return ["summaries: must be an object with version and areas"]
    out: list[str] = []
    version = prd.frontmatter.get("version", "")
    if summaries.get("version") != version:
        out.append(f"summaries: version {summaries.get('version')} is not the PRD's {version}")
    areas = _areas(prd)
    owner = {b.id: a for a, bs in areas.items() for b in bs}
    for name, entry in summaries.get("areas", {}).items():
        if name not in areas:
            out.append(f"summaries: area '{name}' does not exist")
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("text"), str):
            out.append(f"summaries: {name}: must be an object with text and ids")
            continue
        ids = entry.get("ids", [])
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            out.append(f"summaries: {name}: ids must be a list of requirement IDs")
            continue
        for i in entry.get("ids", []):
            if i not in owner:
                out.append(f"summaries: {name}: {i} is not defined")
            elif owner[i] != name:
                out.append(f"summaries: {name}: {i} belongs to area '{owner[i]}'")
        if len(entry["text"]) > MAX_SUMMARY:
            out.append(f"summaries: {name}: text is {len(entry['text'])} characters; at most {MAX_SUMMARY}")
    return out


def id_label(ids: list[str]) -> str:
    """IDs joined with ', '; three or more consecutive numbers of one kind become first–last."""
    parsed = [(m.group(1), int(m.group(2))) if (m := _ID.match(i)) else (i, None) for i in ids]
    out: list[str] = []
    i = 0
    while i < len(ids):
        j = i
        while (parsed[i][1] is not None and j + 1 < len(ids) and parsed[j + 1][0] == parsed[i][0]
               and parsed[j + 1][1] == parsed[j][1] + 1):
            j += 1
        out += [f"{ids[i]}–{ids[j]}"] if j - i >= 2 else ids[i : j + 1]
        i = j + 1
    return ", ".join(out)


def _summary_box(prd: Prd, area: str, summaries: dict | None) -> str:
    entry = ((summaries or {}).get("areas") or {}).get(area)
    if not entry:
        return ""
    ids = entry.get("ids") or []
    version = prd.frontmatter.get("version", "")
    label = L("summary_of_ids", ids=id_label(ids), version=version) if ids else L("summary_of_area", area=area, version=version)
    links = " ".join(f'<a href="#{_e(i)}">{_e(i)}</a>' for i in ids)
    return (f'<div class="summary"><p class="label">{_e(label)}</p><p>{_e(entry["text"])}</p>'
            + (f'<p class="label">{_e(L("blocks"))}: {links}</p>' if links else "") + "</div>")


# ---- blocks ----------------------------------------------------------------------------------

def _chip(status_: str | None) -> str:
    s = status_ or "-"
    cls = re.sub(r"[^a-z]", "", s.lower())
    return f'<span class="chip chip-{cls}">{_e(s)}</span>'


def _block(b: ReqBlock) -> str:
    acs = "".join(
        f'<li id="{_e(a.id)}">' + (f'<span class="removed"><strong>{_e(a.id)}</strong> {_inline(a.text)}</span> ({_e(L("removed"))})'
                                    if a.removed else f"<strong>{_e(a.id)}</strong> {_inline(a.text)}") + "</li>"
        for a in b.acs)
    since = f" {_e(L('since'))} {_e(b.since)}" if b.since else ""
    return (f'<h3 id="{_e(b.id)}">{_e(b.id)} {_inline(b.title)} {_chip(b.status)}<small class="none">{since}</small></h3>'
            + (f"<ul>{acs}</ul>" if acs else ""))


def _area_blocks(prd: Prd, summaries: dict | None, nfr: bool) -> str:
    out = []
    for area, blocks in _areas(prd).items():
        if (area == "nfr") != nfr:
            continue
        out.append(f"<h2>{_e(L('requirements_area', area=area))}</h2>")
        out.append(_summary_box(prd, area, summaries))
        out += [_block(b) for b in blocks if b.kind != "UJ"]
    return "".join(out)


# ---- header ----------------------------------------------------------------------------------

def commit_of(repo_root: Path) -> str:
    """The short HEAD hash of the PRD's repository; `no commit` outside git or in a repository without one."""
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=10, check=True).stdout.strip()
        return out or NO_COMMIT
    except (OSError, subprocess.SubprocessError):
        return NO_COMMIT


def _header(prd: Prd, repo_root: Path, today: date) -> str:
    fm = prd.frontmatter
    st = fm.get("status", "-")
    st_html = _e(st) if st == "Approved" else f'<span class="status-flag">{_e(st)}</span>'
    h1 = _e(_title(prd))
    return (f"<h1>{h1}</h1>\n<dl class=\"facts\">"
            f"<dt>{_e(L('project'))}</dt><dd>{_e(fm.get('prd', '-'))}</dd><dt>{_e(L('prd_version'))}</dt><dd>{_e(fm.get('version', '-'))}</dd>"
            f"<dt>{_e(L('status'))}</dt><dd>{st_html}</dd><dt>{_e(L('commit'))}</dt><dd>{_e(L('no_commit') if commit_of(repo_root) == NO_COMMIT else commit_of(repo_root))}</dd>"
            f"<dt>{_e(L('generated'))}</dt><dd>{_e(today.isoformat())}</dd></dl>")


def _title(prd: Prd) -> str:
    m = re.search(r"^# (.+)$", prd.docs["prd.md"], re.M)
    return m.group(1).strip() if m else prd.frontmatter.get("prd", "PRD")


# ---- business --------------------------------------------------------------------------------

def _deployed(prd: Prd) -> str:
    """The Deployed rows, plus a `not deployed` row for each production environment without one."""
    rows = {r.env: r for r in prd.operations.deployed}
    missing = [e for e in prd.operations.environments if e in production_envs(prd) and e not in rows]
    body = [[_e(r.env), _e(r.version), _e(r.commit), _e(r.date)] for r in rows.values()]
    body += [[_e(e), _e(L("not_deployed")), "", ""] for e in missing]
    return _table([_e(L("environment")), _e(L("prd_version")), _e(L("commit")), _e(L("date"))], body)


def _assumptions(prd: Prd) -> str:
    open_rows = [r for r in prd.assumptions if len(r.cells) >= 3 and r.cells[2].strip("` ").lower() != "confirmed"]
    return _table([_e(L("id")), _e(L("assumption")), _e(L("status"))], [[_inline(c) for c in r.cells[:3]] for r in open_rows])


def _open_entries(prd: Prd) -> str:
    items = [f"<li>{_e(e.id)} {_inline(e.title)}</li>" for e in prd.errors_ledger.values() if e.open]
    return f"<ul>{''.join(items)}</ul>" if items else _none()


def _journeys(prd: Prd) -> str:
    js = [b for b in prd.blocks if b.kind == "UJ"]
    out = []
    for b in js:
        flow = next((t[len("Flow:"):].strip() for _, t in b.lines if t.startswith("Flow:")), "")
        out.append(_block(b) + (f"<p>{_inline(flow)}</p>" if flow else ""))
    return "".join(out) or _none()


def business(prd: Prd, summaries: dict | None) -> str:
    return "\n".join([
        f"<h2>{_e(L('summary_goals'))}</h2>", _section_md(prd, 2),
        f"<h2>{_e(L('glossary'))}</h2>", _section_md(prd, 3),
        f"<h2>{_e(L('user_journeys'))}</h2>", _journeys(prd),
        _area_blocks(prd, summaries, nfr=False),
        f"<h2>{_e(L('open_assumptions'))}</h2>", _assumptions(prd),
        f"<h2>{_e(L('open_questions'))}</h2>", _section_md(prd, 13),
        f"<h2>{_e(L('running_environments'))}</h2>", _deployed(prd),
        f"<h2>{_e(L('open_errors'))}</h2>", _open_entries(prd),
    ])


# ---- technical -------------------------------------------------------------------------------

def _contracts(prd: Prd) -> str:
    ops = sorted(operation_ids(prd))
    tables = schema_tables(prd)
    events = sorted(event_names(prd))
    codes = prd.yaml.get("contracts/errors.yaml")
    code_rows = []
    for code, v in (codes.items() if isinstance(codes, dict) else []):
        d = v if isinstance(v, dict) else {}
        code_rows.append([f"<code>{_e(code)}</code>", _e(d.get("status", "")), _inline(str(d.get("meaning", "")))])

    def names(title: str, items: list[str]) -> str:
        li = "".join(f"<li><code>{_e(i)}</code></li>" for i in items)
        return f"<h3>{title}</h3>" + (f"<ul>{li}</ul>" if li else _none())

    tbl = [f"{t} ({', '.join(sorted(c))})" if c else t for t, c in sorted(tables.items())]
    tl = "".join(f"<li><code>{_e(t)}</code></li>" for t in tbl)
    return (names(_e(L("operations")), ops) + f"<h3>{_e(L('tables'))}</h3>" + (f"<ul>{tl}</ul>" if tl else _none()) + names(_e(L("events")), events)
            + f"<h3>{_e(L('error_codes'))}</h3>" + _table([_e(L("code")), _e(L("status")), _e(L("meaning"))], code_rows))


def _nfrs(prd: Prd, summaries: dict | None) -> str:
    out = [_summary_box(prd, "nfr", summaries)]
    out += [_block(b) for b in prd.blocks if b.kind == "NFR"]
    return "".join(out) if any(b.kind == "NFR" for b in prd.blocks) else _none()


def _matrix(prd: Prd, repo_root: Path) -> str:
    rows = []
    for item in status._matrix(prd, repo_root):
        if item.id is None:
            continue
        block = next(b for b in prd.blocks if b.id == item.id)
        cells = item.text.split(": ", 1)[1]
        if cells == "no tests":
            rows.append([_e(item.id), _chip(block.status), _e(L("no_tests")), "", "", ""])
            continue
        for cell in cells.split("; "):
            tid, level, gate, cited = cell.split(" ")
            rows.append([_e(item.id), _chip(block.status), _e(tid), _e(level), _e(gate), _e(L(cited))])
    return _table([_e(L("requirement")), _e(L("status")), _e(L("test")), _e(L("level")), _e(L("gate")), _e(L("in_code"))], rows)


def _runbook(prd: Prd) -> str:
    out = []
    for s in prd.operations.steps:
        labels = "".join(f"<li><strong>{_e(k)}:</strong> {_inline(v[0])}</li>" for k, v in s.labels.items())
        meta = f" ({_e(s.actor)}, {_e(s.env)})" if s.actor else ""
        out.append(f"<li>{_inline(s.title)}{meta}<ul>{labels}</ul></li>")
    return f"<ol>{''.join(out)}</ol>" if out else _none()


def _ledger(prd: Prd) -> str:
    out = []
    for e in prd.errors_ledger.values():
        facts = [(L("state"), e.state), (L("detected"), e.detected), (L("classification"), e.classification),
                 (L("confirmed"), e.confirmed_raw or ""), (L("touches"), ", ".join(t for t, _ in e.touches)),
                 (L("diagnosis"), e.diagnosis), (L("resolution"), e.resolution), (L("recurrence_of"), e.recurrence)]
        rows = "".join(f"<dt>{_e(k)}</dt><dd>{_inline(v)}</dd>" for k, v in facts if v not in ("", "-"))
        out.append(f'<div class="entry" id="{_e(e.id)}"><h3>{_e(e.id)} {_inline(e.title)}</h3><dl class="facts">{rows}</dl></div>')
    return "".join(out) or _none()


def technical(prd: Prd, repo_root: Path, summaries: dict | None) -> str:
    fm = prd.frontmatter
    meta = "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>" for k, v in fm.items())
    return "\n".join([
        f"<h2>{_e(L('metadata_stack'))}</h2>", f'<dl class="facts">{meta}</dl>', _section_md(prd, 1),
        f"<h2>{_e(L('architecture'))}</h2>", _section_md(prd, 4),
        f"<h2>{_e(L('contracts'))}</h2>", _contracts(prd),
        f"<h2>{_e(L('nfrs'))}</h2>", _nfrs(prd, summaries),
        f"<h2>{_e(L('test_levels'))}</h2>", _doc_section_md(prd, "testing.md", "Levels"),
        f"<h2>{_e(L('matrix'))}</h2>", _matrix(prd, repo_root),
        f"<h2>{_e(L('environments'))}</h2>", _doc_section_md(prd, "operations.md", "Environments"),
        *([f"<h2>{_e(L('links'))}</h2>", _doc_md(prd, "links.md")] if "links.md" in prd.docs else []),
        f"<h2>{_e(L('runbook'))}</h2>", _runbook(prd),
        f"<h2>{_e(L('standards'))}</h2>", _section_md(prd, 5),
        f"<h2>{_e(L('skills'))}</h2>", _section_md(prd, 6),
        f"<h2>{_e(L('contract_types'))}</h2>", _section_md(prd, 7),
        f"<h2>{_e(L('error_ledger'))}</h2>", _ledger(prd),
    ])


# ---- page ------------------------------------------------------------------------------------

def render_page(prd: Prd, repo_root: Path, summaries: dict | None, today: date) -> str:
    if summaries is not None:
        problems = summary_problems(prd, summaries)
        if problems:
            raise Refused(problems)
    _use_language(prd)
    table = languages.for_prd(prd)
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        lang=_e(table.code if table else "en"),
        business_label=_e(L("business")), technical_label=_e(L("technical")),
        title=_e(f"{prd.frontmatter.get('prd', 'PRD')} {L('prd')} {prd.frontmatter.get('version', '')}"),
        header=_header(prd, repo_root, today),
        business=business(prd, summaries),
        technical=technical(prd, repo_root, summaries),
    )
