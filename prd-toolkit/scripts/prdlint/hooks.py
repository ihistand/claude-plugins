"""Vendor the toolkit scripts into a repo and install git hook shims that run the vendored copy."""
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

VENDOR_DIR = ".prd-toolkit"
VENDORED = ("prd_lint.py", "prd_trace.py", "prd_status.py", "prd_context.py", "prd_build_check.py", "prd_hooks.py", "prd_git_hook.py", "prd_deploy.py", "prd_drift.py", "prd_block.py", "prd_error.py", "prd_links.py", "prd_confirm.py", "prd_judge.py", "prd_change.py", "prd_gates.py")
MARKER = "# prd-toolkit hook"
HOOKS = ("commit-msg", "pre-commit")
BLOCK_TEMPLATE = "claude-block.md"
CONFIRM_PANEL = "confirm/panel.html"
INBOX_PAGE = "gates/inbox.html"  # templates/gates/inbox.html in the plugin, .prd-toolkit/gates/inbox.html vendored
CONFIRM_PAGE = "confirm/form.html"  # templates/confirm/form.html in the plugin, .prd-toolkit/confirm/form.html vendored
JUDGE_DIR = "judge"  # templates/judge/ in the plugin, .prd-toolkit/judge/ vendored
LANGUAGES_DIR = "languages"  # references/languages/ in the plugin, .prd-toolkit/languages/ vendored
PACKS_DIR = "packs"  # .prd-toolkit/packs/<name>/
PACK_SOURCES = "pack-sources.json"  # .prd-toolkit/pack-sources.json: {"<pack name>": "<source>"} of each vendored pack
RECORD_DIR = ".prd-judge/"
REVIEW_FILE = ".prd-review.json"  # the review verdict review mode or the changing-prds skill writes; never committed
BLOCK_TEMPLATE_DIR = "templates"  # .prd-toolkit/templates/claude-block.md
HOMEPAGE_FILE = "HOMEPAGE"  # .prd-toolkit/HOMEPAGE: the plugin's `homepage`, one line, read by a vendored prd_block.py
VENDORED_TEMPLATES = "hooks"  # the shim templates, vendored as .prd-toolkit/hooks/

SCRIPTS = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SCRIPTS.parent


def is_plugin() -> bool:
    """True when running from the plugin: this directory is `scripts` and its parent holds .claude-plugin/plugin.json."""
    return SCRIPTS.name == "scripts" and (PLUGIN_ROOT / ".claude-plugin/plugin.json").is_file()


def _ours(path: Path) -> bool:
    """A hook we wrote: the marker opens its second line."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return False
    return len(lines) > 1 and lines[1].startswith(MARKER)


def _quote(s: str) -> str:
    """Escape for use inside double quotes in sh."""
    for ch in ("\\", '"', "$", "`"):
        s = s.replace(ch, "\\" + ch)
    return s


def _hooks_path_config(repo_root: Path) -> str:
    r = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=repo_root, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip()


def plugin_version(plugin_root: Path) -> str:
    return json.loads((plugin_root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]


def _template_dir() -> Path:
    return PLUGIN_ROOT / "templates/hooks" if is_plugin() else SCRIPTS / VENDORED_TEMPLATES


def _source_files(scripts: Path, templates: Path) -> dict[str, Path]:
    """Vendored relative path -> source file."""
    files = {name: scripts / name for name in VENDORED}
    for f in sorted((scripts / "prdlint").rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
            files[f.relative_to(scripts).as_posix()] = f
    for hook in HOOKS:
        files[f"{VENDORED_TEMPLATES}/{hook}"] = templates / hook
    files[f"{BLOCK_TEMPLATE_DIR}/{BLOCK_TEMPLATE}"] = templates.parent / BLOCK_TEMPLATE  # prd_block.py reads it from the copy
    for readme in ("readme-prd.md", "readme-prds.md"):  # the README blocks' templates, read the same way
        files[f"{BLOCK_TEMPLATE_DIR}/{readme}"] = templates.parent / readme
    files[CONFIRM_PAGE] = templates.parent / CONFIRM_PAGE
    files[CONFIRM_PANEL] = templates.parent / CONFIRM_PANEL  # form.html includes it
    files[INBOX_PAGE] = templates.parent / INBOX_PAGE  # and so does the inbox page
    for f in sorted((templates.parent / JUDGE_DIR).rglob("*")):
        if f.is_file():
            files[f"{JUDGE_DIR}/{f.relative_to(templates.parent / JUDGE_DIR).as_posix()}"] = f
    for f in sorted((scripts.parent / "references" / LANGUAGES_DIR).glob("*.yaml")):
        files[f"{LANGUAGES_DIR}/{f.name}"] = f
    return files


class InstallRefused(Exception):
    """An install that vendors nothing: a named pack cannot be resolved from its source."""


class BlocksRefused(InstallRefused):
    """An install that writes nothing: a managed block cannot be merged (a broken marker); exit 1, not an internal error."""


def _pack_refs(prd) -> list:
    """Every pack to vendor: the ones the PRD names, then `service`, one per name."""
    from . import packs

    refs = list(packs.named(prd))
    if not any(r.name == "service" for r in refs):
        refs.append(packs.SERVICE_DEFAULT)
    out, seen = [], set()
    for r in refs:
        if r.name not in seen:
            seen.add(r.name)
            out.append(r)
    return out


def _resolve_sources(repo_root: Path, prd) -> list:
    """The source Pack of each ref, or InstallRefused naming where it looked."""
    from . import packs

    out = []
    for ref in _pack_refs(prd):
        try:
            out.append(packs.resolve(ref, repo_root, vendored=False))
        except packs._FAILURES as e:
            raise InstallRefused(str(e)) from None
    return out


def _pack_tree(folder: Path) -> dict[str, bytes]:
    return {f.relative_to(folder).as_posix(): f.read_bytes() for f in sorted(folder.rglob("*"))
            if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc"}


def _ignore_record(repo_root: Path) -> None:
    """Append `.prd-judge/` and `.prd-review.json` to the root .gitignore, each once."""
    path = repo_root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {ln.strip() for ln in text.splitlines()}
    missing = [e for e in (RECORD_DIR, REVIEW_FILE) if e not in have]
    if not missing:
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + ("" if not text or text.endswith("\n") else "\n") + "".join(e + "\n" for e in missing))


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()


def _hooks_dir(repo_root: Path) -> tuple[Path, str]:
    """(directory, display path) of the git hooks directory; worktrees and custom git dirs included."""
    raw = _git(repo_root, "rev-parse", "--git-path", "hooks")
    p = Path(raw)
    return (p if p.is_absolute() else repo_root / p), raw


def _plugin_homepage() -> str | None:
    try:
        value = json.loads((PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8")).get("homepage")
    except (OSError, ValueError, AttributeError):
        return None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _write_homepage(dest: Path) -> None:
    """Write .prd-toolkit/HOMEPAGE (via a temp file) when the plugin has a homepage; remove a stale one otherwise."""
    home, target = _plugin_homepage(), dest / HOMEPAGE_FILE
    if home is None:
        target.unlink(missing_ok=True)
        return
    tmp = dest / f".{HOMEPAGE_FILE}.tmp"
    tmp.write_text(home + "\n", encoding="utf-8")
    os.replace(tmp, target)


def _blocks(repo_root: Path, prd_rel: str):
    """prd_block's targets for the PRD; its module comes from this copy's scripts folder (the vendored one when vendored)."""
    import sys

    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import prd_block
    from .model import load

    prd = load(Path(repo_root) / prd_rel)
    return prd_block, prd_block.targets(prd, Path(repo_root).resolve(), Path(repo_root) / "CLAUDE.md")


def _relative_message(repo_root: Path, text: str) -> str:
    return text.replace(str(Path(repo_root).resolve()) + os.sep, "").replace(str(Path(repo_root)) + os.sep, "")


def _shown(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _vendor(repo_root: Path, sources_packs=()) -> None:
    dest = repo_root / VENDOR_DIR
    sources = _source_files(SCRIPTS, PLUGIN_ROOT / "templates/hooks")
    dest.mkdir(exist_ok=True)
    for rel, src in sources.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    for sub in ("prdlint", VENDORED_TEMPLATES, "confirm", "gates", JUDGE_DIR, LANGUAGES_DIR):
        base = dest / sub
        if base.is_dir():
            for f in sorted(base.rglob("*"), reverse=True):
                rel = f.relative_to(dest).as_posix()
                if f.is_file() and rel not in sources:
                    f.unlink()
                elif f.is_dir() and "__pycache__" in f.parts or (f.is_dir() and not any(f.iterdir())):
                    shutil.rmtree(f, ignore_errors=True)
    packs_dest = dest / PACKS_DIR
    packs_dest.mkdir(exist_ok=True)
    keep = {p.name for p in sources_packs}
    for old in packs_dest.iterdir():
        if old.name not in keep:
            shutil.rmtree(old, ignore_errors=True) if old.is_dir() else old.unlink()
    for pack in sources_packs:
        target = packs_dest / pack.name
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(pack.root, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    record = {p.name: p.source for p in sorted(sources_packs, key=lambda p: p.name)}
    (dest / PACK_SOURCES).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (dest / "VERSION").write_text(plugin_version(PLUGIN_ROOT) + "\n", encoding="utf-8")
    _write_homepage(dest)
    (dest / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")


GUARD = 'command -v uv >/dev/null 2>&1 || { echo "prd-toolkit: uv is not on PATH; install uv to run this hook" >&2; exit 1; }'


SKIP = "prd-toolkit: no .prd-toolkit/ (or no PRD folder) on this branch; hook skipped"


def _append_line(hook: str, prd_rel: str) -> str:
    """One sh line for an existing hook: skips on a branch without the copy or the PRD, blocks without uv."""
    script, prd = f'"$prd_top/{VENDOR_DIR}/prd_git_hook.py"', f'"$prd_top/{_quote(prd_rel)}"'
    return (f'prd_top="$(git rev-parse --show-toplevel)" || exit 1; if [ -f {script} ] && [ -d {prd} ]; then {GUARD}; '
            f'uv run --script {script} {hook} {prd} "$@" || exit $?; else echo "{SKIP}" >&2; fi')


def _append_message(hook: str, prd_rel: str, shown: str, why: str) -> str:
    return (f"{why}; add this line to {shown}/{hook} (an sh hook; place it before any `exit 0` in it): "
            + _append_line(hook, prd_rel))


def _vendor_from_plugin(repo_root: Path, prd_rel: str) -> str:
    """Resolve the PRD's packs, then write .prd-toolkit/; the one path `install` and `vendor` share. Returns the report line."""
    from .model import load  # local: the model imports this package

    sources_packs = _resolve_sources(repo_root, load(repo_root / prd_rel))  # before anything is copied
    _vendor(repo_root, sources_packs)
    return f"vendored the toolkit into {VENDOR_DIR}/ (version {plugin_version(PLUGIN_ROOT)})"


def vendor(repo_root: Path, prd_rel: str) -> list[str]:
    """Refresh .prd-toolkit/ exactly as `install` does, and write nothing else: no hooks, no .gitignore entries."""
    return [_vendor_from_plugin(Path(repo_root), prd_rel)]


def install(repo_root: Path, prd_rel: str) -> list[str]:
    repo_root = Path(repo_root)
    lines: list[str] = []
    module = tgts = None
    if is_plugin():
        module, tgts = _blocks(repo_root, prd_rel)
        try:
            module.stale(tgts)  # merges every block in memory: a broken marker refuses here, before anything is written
        except module.BlockError as e:
            raise BlocksRefused(f"{_relative_message(repo_root, str(e))}; fix the marker, then run prd_block.py {prd_rel}") from None
        lines.append(_vendor_from_plugin(repo_root, prd_rel))
        _ignore_record(repo_root)
    configured = _hooks_path_config(repo_root)
    hooks_dir, shown = _hooks_dir(repo_root)
    if configured:
        for hook in HOOKS:
            lines.append(_append_message(hook, prd_rel, shown, f"core.hooksPath is set to {configured}; no shim written"))
        return lines + _refresh(repo_root, module, tgts)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for hook in HOOKS:
        path = hooks_dir / hook
        if path.exists() and not _ours(path):
            lines.append(_append_message(hook, prd_rel, shown, f"{shown}/{hook} already exists and was left alone"))
            continue
        text = (_template_dir() / hook).read_text(encoding="utf-8").replace("{{hook}}", hook).replace("{{prd}}", _quote(prd_rel))
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        path.chmod(0o755)
        lines.append(f"installed {shown}/{hook}")
    return lines + _refresh(repo_root, module, tgts)


def _refresh(repo_root: Path, module, tgts) -> list[str]:
    """Write the managed blocks (the plugin's prd_block, so a refresh and CI's check agree); the last install step."""
    return [f"refreshed {_shown(repo_root, p)}" for p in module.write(tgts)] if module is not None else []


def not_a_checkout(prd) -> str:
    """Why the CI files cannot be checked: without a checkout, the CI files' place is unknown."""
    return f"{prd.root.as_posix()} is not inside a git checkout"


def stale_ci(repo_root: Path, prd, prd_rel: str) -> list[str]:
    """One line per stale managed block (CLAUDE.md, the PRD's README, the parent README) and per CI include present whose
    text differs from what `prd_hooks.py ci` would write now. A block with a broken marker is one stale line naming the
    file and the problem, so the check exits 1, not 2."""
    jobs = ci_jobs(prd, prd_rel) + deploy_jobs(prd, prd_rel)
    out = []
    module, tgts = _blocks(repo_root, prd_rel)
    try:
        for path in module.stale(tgts):
            out.append(f"stale: {_shown(repo_root, path)}; run prd_block.py {prd_rel}")
    except module.BlockError as e:
        out.append(f"stale: {_relative_message(repo_root, str(e))}; run prd_block.py {prd_rel}")
    for kind, rel in CI_FILES.items():
        path = Path(repo_root) / rel
        if path.is_file() and path.read_text(encoding="utf-8") != (render_gitlab if kind == "gitlab" else render_github)(jobs, prd.operations.secrets):
            out.append(f"stale: {rel}: re-run prd_hooks.py ci --{kind} --force")
    return out


def vendored_sources(vendor_dir: Path) -> dict[str, str]:
    """The source each vendored pack was copied from, by `_vendor`'s pack-sources.json; {} when it does not read."""
    try:
        data = json.loads((Path(vendor_dir) / PACK_SOURCES).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, str)} if isinstance(data, dict) else {}


def _stale_packs(repo_root: Path, prd) -> list[str]:
    """One line per vendored pack that is missing, differs from its source, or was vendored from another source."""
    out = []
    recorded = vendored_sources(repo_root / VENDOR_DIR)
    for ref in _pack_refs(prd):
        try:
            src = _resolve_sources_one(repo_root, ref)
        except InstallRefused:
            continue  # pack-resolves reports a pack that cannot be found
        vend = repo_root / VENDOR_DIR / PACKS_DIR / ref.name
        what = f"{src.source} {src.version}"
        if not vend.is_dir():
            out.append(f"{PACKS_DIR}/{ref.name}: missing; source {what}; run prd_hooks.py install")
        elif _pack_tree(vend) != _pack_tree(src.root):
            out.append(f"{PACKS_DIR}/{ref.name}: differs from {what}; run prd_hooks.py install")
        elif recorded.get(ref.name) != src.source:
            was = recorded.get(ref.name) or "an unrecorded source"
            out.append(f"{PACKS_DIR}/{ref.name}: vendored from {was}, the PRD names {src.source}; run prd_hooks.py install")
    return out


def _resolve_sources_one(repo_root: Path, ref):
    from . import packs

    try:
        return packs.resolve(ref, repo_root, vendored=False)
    except packs._FAILURES as e:
        raise InstallRefused(str(e)) from None


def check(repo_root: Path, plugin_root: Path, prd=None, prd_rel: str = "") -> list[str]:
    repo_root, plugin_root = Path(repo_root), Path(plugin_root)
    dest = repo_root / VENDOR_DIR
    if not dest.is_dir():
        return [f"{VENDOR_DIR}/ is missing; run prd_hooks.py install"]
    problems: list[str] = []
    version = (dest / "VERSION").read_text(encoding="utf-8").strip() if (dest / "VERSION").is_file() else "(none)"
    current = plugin_version(plugin_root)
    if version != current:
        problems.append(f"{VENDOR_DIR}/VERSION {version} differs from the plugin version {current}")
    sources = _source_files(plugin_root / "scripts", plugin_root / "templates/hooks")
    for rel, src in sources.items():
        target = dest / rel
        if not target.is_file():
            problems.append(f"{VENDOR_DIR}/{rel} is missing")
        elif target.read_bytes() != src.read_bytes():
            problems.append(f"{VENDOR_DIR}/{rel} differs from the plugin copy")
    for sub in ("prdlint", VENDORED_TEMPLATES, "confirm", "gates", JUDGE_DIR, LANGUAGES_DIR):
        for f in sorted((dest / sub).rglob("*")) if (dest / sub).is_dir() else []:
            rel = f.relative_to(dest).as_posix()
            if f.is_file() and "__pycache__" not in f.parts and rel not in sources:
                problems.append(f"{VENDOR_DIR}/{rel} is not in the plugin")
    if prd is not None:
        problems += _stale_packs(repo_root, prd)
        problems += stale_ci(repo_root, prd, prd_rel)
    return problems


def uninstall(repo_root: Path) -> list[str]:
    configured = _hooks_path_config(Path(repo_root))
    if configured:
        return [f"core.hooksPath is set to {configured}; removed nothing"]
    hooks_dir, shown = _hooks_dir(Path(repo_root))
    lines: list[str] = []
    for hook in HOOKS:
        path = hooks_dir / hook
        if path.is_file() and _ours(path):
            path.unlink()
            lines.append(f"removed {shown}/{hook}")
    return lines


CI_FILES = {"gitlab": ".gitlab/prd-toolkit.yml", "github": ".github/workflows/prd-toolkit.yml"}
RANGE = "@RANGE@"  # the merge-base range, filled in by each renderer
GITLAB_IMAGE = "python:3.12"
GITLAB_RANGE = "$CI_MERGE_REQUEST_DIFF_BASE_SHA..HEAD"
GITHUB_RANGE = "${{ github.event.pull_request.base.sha }}..HEAD"


@dataclass(frozen=True)
class CiJob:
    name: str
    script: list[str]
    manual: bool = False  # a manual job: never part of the merge gate, started by hand


def job_id(name: str) -> str:
    """A CI job id matching ^[_A-Za-z][\\w-]*$: other characters become `-`, and a bad first character gains a `_`."""
    out = re.sub(r"[^A-Za-z0-9_-]", "-", name)
    return out if re.match(r"[_A-Za-z]", out) else "_" + out


def _dedupe(jobs: list[CiJob]) -> list[CiJob]:
    """Sanitize every id; a repeat gains `-2`, `-3`, … in job order, skipping any id already taken."""
    taken: set[str] = set()
    out = []
    for j in jobs:
        base = name = job_id(j.name)
        n = 1
        while name in taken:
            n += 1
            name = f"{base}-{n}"
        taken.add(name)
        out.append(CiJob(name, j.script, j.manual))
    return out


def ci_jobs(prd, prd_rel: str) -> list[CiJob]:
    """The merge-gate jobs for a PRD: lint, trace, one per enforced standards row, one per build-gate level."""
    from .model import gate_of
    from .rules.registries import standards_rows

    q = shlex.quote(prd_rel)
    out = [CiJob("prd-lint", [f"uv run --script {VENDOR_DIR}/prd_lint.py --ci {q}", f"uv run --script {VENDOR_DIR}/prd_hooks.py check --ci {q}"]),
           CiJob("prd-trace", [f"uv run --script {VENDOR_DIR}/prd_trace.py {q} --range {RANGE}"])]
    if prd.links is not None:
        out[0].script.append(f"uv run --script {VENDOR_DIR}/prd_links.py check --ci {q}")
    n = 0
    for row in standards_rows(prd):
        if row.decision == "enforced" and row.command:
            n += 1
            # ./%(path): a path starting with `-` must not read as an option to the linter
            out.append(CiJob(f"standards-{n}", [f"git ls-files -z --format='./%(path)' -- {shlex.quote(':(glob)' + row.glob)} | xargs -0 -r {row.command}"]))
    for level in prd.testing.levels:
        if gate_of(prd, level) == "build" and level in prd.testing.commands:
            out.append(CiJob(f"test-{level}", [prd.testing.commands[level]]))
    return _dedupe(out)


def deploy_jobs(prd, prd_rel: str) -> list[CiJob]:
    """The manual jobs: `drift-<env>` per environment with a Drift row, then `test-deploy-<env>` per environment with a tests step,
    each group in Environments order. Ids are deduplicated against the merge-gate jobs. CI never runs prd_deploy.py."""
    ops = prd.operations
    q = shlex.quote(prd_rel)
    drift_envs = {r.env for r in ops.drift}
    raw = [CiJob(f"drift-{env}", [f"uv run --script {VENDOR_DIR}/prd_drift.py {q} --env {shlex.quote(env)}"], True) for env in ops.environments if env in drift_envs]
    for env in ops.environments:
        levels = [lv for s in ops.steps if s.env == env and s.tests for lv in s.tests]
        if not any(s.env == env and s.tests is not None for s in ops.steps):
            continue
        # exported, so a compound command (`cd tools && bash gate.sh`) sees them past its first word
        script = [f"export PRD_ENV={shlex.quote(env)} TEST_ENV={shlex.quote(env)}; {prd.testing.commands[lv]}" for lv in levels if lv in prd.testing.commands]
        if script:  # an empty job is invalid CI
            raw.append(CiJob(f"test-deploy-{env}", script, True))
    base = ci_jobs(prd, prd_rel)
    return _dedupe(base + raw)[len(base):]


def _secrets_line(jobs: list[CiJob], secrets) -> list[str]:
    if secrets and any(j.manual for j in jobs):
        return ["# Manual jobs may need these secrets (operations.md Secrets): " + ", ".join(secrets)]
    return []


def _q(s: str) -> str:
    """A YAML double-quoted scalar (JSON strings are valid YAML)."""
    return json.dumps(s, ensure_ascii=False)


def render_gitlab(jobs: list[CiJob], secrets=()) -> str:
    lines = ["# Generated by prd_hooks.py ci --gitlab; regenerate rather than edit.", *_secrets_line(jobs, secrets), ""]
    for j in jobs:
        lines += [f"{j.name}:", f"  image: {GITLAB_IMAGE}", "  rules:"]
        if j.manual:
            lines += ["    - when: manual", "  allow_failure: true"]
        else:
            lines.append('    - if: \'$CI_PIPELINE_SOURCE == "merge_request_event"\'')
        if j.name == "prd-trace":
            lines += ["  variables:", '    GIT_DEPTH: "0"']
        lines += ["  before_script:", f"    - {_q('pip install uv')}", "  script:"]
        lines += [f"    - {_q(s.replace(RANGE, GITLAB_RANGE))}" for s in j.script]
        lines.append("")
    return "\n".join(lines)


def render_github(jobs: list[CiJob], secrets=()) -> str:
    manual = any(j.manual for j in jobs)
    lines = ["# Generated by prd_hooks.py ci --github; regenerate rather than edit.", *_secrets_line(jobs, secrets), "name: prd-toolkit", "on:", "  pull_request:"]
    if manual:
        lines.append("  workflow_dispatch:")
    lines += ["", "permissions:", "  contents: read", "", "jobs:"]
    for j in jobs:
        lines.append(f"  {j.name}:")
        if manual:
            lines.append(f"    if: {_q('github.event_name == ' + chr(39) + ('workflow_dispatch' if j.manual else 'pull_request') + chr(39))}")
        lines += ["    runs-on: ubuntu-latest", "    steps:", "      - uses: actions/checkout@v4", "        with:", "          fetch-depth: 0",
                  "      - uses: astral-sh/setup-uv@v5"]
        for s in j.script:
            lines.append(f"      - run: {_q(s.replace(RANGE, GITHUB_RANGE))}")
        lines.append("")
    return "\n".join(lines)


def write_ci(repo_root: Path, kind: str, jobs: list[CiJob], force: bool, secrets=()) -> tuple[int, list[str]]:
    """Write CI_FILES[kind]. (0, lines) on a write or an identical file; (1, diff) when a different file exists and force is off."""
    text = (render_gitlab if kind == "gitlab" else render_github)(jobs, secrets)
    path = Path(repo_root) / CI_FILES[kind]
    if path.is_file():
        old = path.read_text(encoding="utf-8")
        if old != text and not force:
            diff = difflib.unified_diff(old.splitlines(), text.splitlines(), f"{CI_FILES[kind]} (existing)", f"{CI_FILES[kind]} (generated)", lineterm="")
            return 1, [*diff, f"{CI_FILES[kind]} exists and differs; rerun with --force to overwrite it"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    lines = [f"wrote {CI_FILES[kind]}"]
    if kind == "gitlab":
        lines.append(f"include: '{CI_FILES[kind]}'")
    return 0, lines
