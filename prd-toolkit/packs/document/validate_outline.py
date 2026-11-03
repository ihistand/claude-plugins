#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate contracts/outline.yaml files of the document pack. Run from the PRD root with the files as arguments;
a document `path` is relative to the repository root.
Exit 0 clean, 1 findings on stderr (`<file>: <key>: <problem>`), 2 usage or dependency error."""
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

try:
    import yaml
except ImportError:
    print("validate_outline: missing Python package 'pyyaml'. Run with: uv run --script validate_outline.py <files>…, "
          "or: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REQUIRED = ("path", "audience", "purpose")


def _strings(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def repo_root(cwd: Path) -> Path:
    """The repository root a document `path` is relative to: the nearest ancestor holding `.git`; else the third
    ancestor of a PRD folder at `<root>/docs/prd/<name>`; else the PRD root itself."""
    for d in (cwd, *cwd.parents):
        if (d / ".git").exists():
            return d
    if cwd.parent.name == "prd" and cwd.parent.parent.name == "docs":
        return cwd.parent.parent.parent
    return cwd


def check_entry(key: str, entry) -> list[str]:
    """The problems of one outline entry, each starting with `<key>: `."""
    if not isinstance(entry, dict):
        return [f"{key}: must be a mapping"]
    out = []
    for k in REQUIRED:
        if not (isinstance(entry.get(k), str) and entry[k].strip()):
            out.append(f"{key}: missing {k}")
    path = entry.get("path")
    if isinstance(path, str) and path.strip():
        if PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute() or not path.endswith(".md"):
            out.append(f"{key}: path must be a relative .md path")
        else:
            cwd = Path.cwd().resolve()
            if (repo_root(cwd) / path).resolve().is_relative_to(cwd):
                out.append(f"{key}: path must be outside the PRD folder")
    if not (_strings(entry.get("sections")) and entry["sections"]):
        out.append(f"{key}: sections must be a non-empty list of strings")
    if "terms" in entry and not _strings(entry["terms"]):
        out.append(f"{key}: terms must be a list of strings")
    if "length" in entry:
        length = entry["length"]
        if not isinstance(length, dict):
            out.append(f"{key}: length must be a mapping with min-words and max-words")
        else:
            ok = True
            for k in ("min-words", "max-words"):
                if k in length and not _int(length[k]):
                    out.append(f"{key}: length: {k} must be an integer")
                    ok = False
            if ok and _int(length.get("min-words")) and _int(length.get("max-words")) and length["min-words"] > length["max-words"]:
                out.append(f"{key}: length: min-words must not exceed max-words")
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_outline.py <outline.yaml>…  (run from the PRD root)", file=sys.stderr)
        return 2
    problems: list[str] = []
    for rel in argv:
        try:
            data = yaml.safe_load(Path(rel).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as e:
            problems.append(f"{rel}: {str(e).splitlines()[0] if str(e) else 'unreadable'}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{rel}: top level must be a mapping with one key per document")
            continue
        for key, entry in data.items():
            problems += [f"{rel}: {p}" for p in check_entry(str(key), entry)]
    for p in problems:
        print(p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
