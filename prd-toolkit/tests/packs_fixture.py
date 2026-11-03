"""Fixture packs and an installed-plugins file for the pack tests (0.8.0). Packs are written in tmp dirs, never in packs/."""
import json
from pathlib import Path

import yaml

TOOLKIT = ">=0.8.0,<0.9"  # the tests pin packs.toolkit_version to 0.8.0


def write_pack(dir: Path, name: str, version: str | None, **keys) -> Path:
    """Write `dir/<name>/pack.yaml` and return the pack folder. A key's underscores become hyphens
    (`contract_types` -> `contract-types`); `version=None` or a key set to None leaves it out; `pack` and `toolkit`
    default to the name and TOOLKIT."""
    folder = Path(dir) / name
    folder.mkdir(parents=True, exist_ok=True)
    data = {"pack": name, "version": version, "toolkit": TOOLKIT}
    data.update({k.replace("_", "-"): v for k, v in keys.items()})
    data = {k: v for k, v in data.items() if v is not None}
    (folder / "pack.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return folder


def plugins_file(tmp: Path, installs: dict[str, Path]) -> Path:
    """An installed_plugins.json at tmp/installed_plugins.json with one user-scope install per plugin key."""
    path = Path(tmp) / "installed_plugins.json"
    plugins = {key: [{"scope": "user", "installPath": str(p), "version": "1.0.0"}] for key, p in installs.items()}
    path.write_text(json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")
    return path
