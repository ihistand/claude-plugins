"""Vendor the toolkit scripts into a repo and install git hook shims that run the vendored copy."""
import difflib
import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

VENDOR_DIR = ".prd-toolkit"
VENDORED = ("prd_lint.py", "prd_trace.py", "prd_status.py", "prd_context.py", "prd_build_check.py", "prd_hooks.py", "prd_git_hook.py")
MARKER = "# prd-toolkit hook"
HOOKS = ("commit-msg", "pre-commit")
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
    return files


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()


def _hooks_dir(repo_root: Path) -> tuple[Path, str]:
    """(directory, display path) of the git hooks directory; worktrees and custom git dirs included."""
    raw = _git(repo_root, "rev-parse", "--git-path", "hooks")
    p = Path(raw)
    return (p if p.is_absolute() else repo_root / p), raw


def _vendor(repo_root: Path) -> None:
    dest = repo_root / VENDOR_DIR
    sources = _source_files(SCRIPTS, PLUGIN_ROOT / "templates/hooks")
    dest.mkdir(exist_ok=True)
    for rel, src in sources.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    for sub in ("prdlint", VENDORED_TEMPLATES):
        base = dest / sub
        if base.is_dir():
            for f in sorted(base.rglob("*"), reverse=True):
                rel = f.relative_to(dest).as_posix()
                if f.is_file() and rel not in sources:
                    f.unlink()
                elif f.is_dir() and "__pycache__" in f.parts or (f.is_dir() and not any(f.iterdir())):
                    shutil.rmtree(f, ignore_errors=True)
    (dest / "VERSION").write_text(plugin_version(PLUGIN_ROOT) + "\n", encoding="utf-8")


GUARD = 'command -v uv >/dev/null 2>&1 || { echo "prd-toolkit: uv is not on PATH; install uv to run this hook" >&2; exit 1; }'


def _append_line(hook: str, prd_rel: str) -> str:
    top = '"$(git rev-parse --show-toplevel)'
    return (f'{GUARD}; uv run --script {top}/{VENDOR_DIR}/prd_git_hook.py" {hook} {top}/{_quote(prd_rel)}" "$@" || exit $?')


def _append_message(hook: str, prd_rel: str, shown: str, why: str) -> str:
    return (f"{why}; add this line to {shown}/{hook} (an sh hook; place it before any `exit 0` in it): "
            + _append_line(hook, prd_rel))


def install(repo_root: Path, prd_rel: str) -> list[str]:
    repo_root = Path(repo_root)
    lines: list[str] = []
    if is_plugin():
        _vendor(repo_root)
        lines.append(f"vendored the toolkit into {VENDOR_DIR}/ (version {plugin_version(PLUGIN_ROOT)})")
    configured = _hooks_path_config(repo_root)
    hooks_dir, shown = _hooks_dir(repo_root)
    if configured:
        for hook in HOOKS:
            lines.append(_append_message(hook, prd_rel, shown, f"core.hooksPath is set to {configured}; no shim written"))
        return lines
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
    return lines


def check(repo_root: Path, plugin_root: Path) -> list[str]:
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
    for sub in ("prdlint", VENDORED_TEMPLATES):
        for f in sorted((dest / sub).rglob("*")) if (dest / sub).is_dir() else []:
            rel = f.relative_to(dest).as_posix()
            if f.is_file() and "__pycache__" not in f.parts and rel not in sources:
                problems.append(f"{VENDOR_DIR}/{rel} is not in the plugin")
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


def ci_jobs(prd, prd_rel: str) -> list[CiJob]:
    """The merge-gate jobs for a PRD: lint, trace, one per enforced standards row, one per build-gate level."""
    from .model import gate_of
    from .rules.registries import standards_rows

    q = shlex.quote(prd_rel)
    out = [CiJob("prd-lint", [f"uv run --script {VENDOR_DIR}/prd_lint.py --ci {q}"]),
           CiJob("prd-trace", [f"uv run --script {VENDOR_DIR}/prd_trace.py {q} --range {RANGE}"])]
    n = 0
    for row in standards_rows(prd):
        if row.decision == "enforced" and row.command:
            n += 1
            out.append(CiJob(f"standards-{n}", [f"git ls-files -z -- {shlex.quote(':(glob)' + row.glob)} | xargs -0 -r {row.command}"]))
    for level in prd.testing.levels:
        if gate_of(prd, level) == "build" and level in prd.testing.commands:
            out.append(CiJob(f"test-{level}", [prd.testing.commands[level]]))
    return out


def _q(s: str) -> str:
    """A YAML double-quoted scalar (JSON strings are valid YAML)."""
    return json.dumps(s, ensure_ascii=False)


def render_gitlab(jobs: list[CiJob]) -> str:
    lines = ["# Generated by prd_hooks.py ci --gitlab; regenerate rather than edit.", ""]
    for j in jobs:
        lines += [f"{j.name}:", f"  image: {GITLAB_IMAGE}", "  rules:", '    - if: \'$CI_PIPELINE_SOURCE == "merge_request_event"\'']
        if j.name == "prd-trace":
            lines += ["  variables:", '    GIT_DEPTH: "0"']
        lines += ["  before_script:", f"    - {_q('pip install uv')}", "  script:"]
        lines += [f"    - {_q(s.replace(RANGE, GITLAB_RANGE))}" for s in j.script]
        lines.append("")
    return "\n".join(lines)


def render_github(jobs: list[CiJob]) -> str:
    lines = ["# Generated by prd_hooks.py ci --github; regenerate rather than edit.", "name: prd-toolkit", "on:", "  pull_request:", "", "jobs:"]
    for j in jobs:
        lines += [f"  {j.name}:", "    runs-on: ubuntu-latest", "    steps:", "      - uses: actions/checkout@v4", "        with:", "          fetch-depth: 0",
                  "      - uses: astral-sh/setup-uv@v5"]
        for s in j.script:
            lines.append(f"      - run: {_q(s.replace(RANGE, GITHUB_RANGE))}")
        lines.append("")
    return "\n".join(lines)


def write_ci(repo_root: Path, kind: str, jobs: list[CiJob], force: bool) -> tuple[int, list[str]]:
    """Write CI_FILES[kind]. (0, lines) on a write or an identical file; (1, diff) when a different file exists and force is off."""
    text = (render_gitlab if kind == "gitlab" else render_github)(jobs)
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
