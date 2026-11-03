"""PRD language tables: EARS openers and vague words per language (`language:` in the PRD frontmatter)."""
import re
from dataclasses import dataclass
from pathlib import Path

from .deps import require

SCRIPTS = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SCRIPTS.parent


def is_plugin() -> bool:
    """True when running from the plugin: this directory is `scripts` and its parent holds .claude-plugin/plugin.json."""
    return SCRIPTS.name == "scripts" and (PLUGIN_ROOT / ".claude-plugin/plugin.json").is_file()


def toolkit_dir() -> Path:
    """The toolkit's own tables: `references/languages/` in the plugin, `languages/` beside the scripts when vendored."""
    return PLUGIN_ROOT / "references/languages" if is_plugin() else SCRIPTS / "languages"


TABLES_DIR = toolkit_dir()
_META = re.compile(r"([.^$*+?{}\[\]\\|()])")


@dataclass
class Table:
    code: str
    openers: list[str]
    ubiquitous: re.Pattern
    vague: re.Pattern
    labels: dict[str, str]
    ubiquitous_hint: str = ""
    modal: re.Pattern | None = None  # the verb every AC must carry; None skips that check
    modal_word: str = ""

    def opener(self) -> re.Pattern:
        return re.compile(r"^(?:" + "|".join(_META.sub(r"\\\1", o) for o in self.openers) + r")\b")

    def ears_message(self, ac_id: str) -> str:
        return f"{ac_id} must start with {', '.join(self.openers)} or {self.ubiquitous_hint}"


def _build(code: str, data: dict) -> Table:
    ears = data.get("ears") or {}
    words = "|".join(_META.sub(r"\\\1", w) for w in data.get("vague") or [])
    modal = ears.get("modal")
    return Table(
        code=code,
        openers=list(ears.get("openers") or []),
        ubiquitous=re.compile(ears["ubiquitous"]),
        vague=re.compile(rf"\b({words})\b", re.I),
        labels=dict(data.get("labels") or {}),
        ubiquitous_hint=ears.get("ubiquitous_hint", ""),
        modal=re.compile(modal) if modal else None,
        modal_word=ears.get("modal_word", ""),
    )


# 0.7's table, used only when a vendored copy has no languages/ folder yet (older vendoring), so lint output never changes
_EN = {
    "ears": {"openers": ["When", "While", "If", "Where"], "ubiquitous": r"^The \S.*? shall\b", "ubiquitous_hint": "'The <thing> shall'", "modal": r"\bshall\b", "modal_word": "shall"},
    "vague": ["fast", "secure", "scalable", "robust", "intuitive", "seamless", "user-friendly"],
}


def load(code: str, extra_dirs=()) -> Table | None:
    """The table for `code`: the toolkit's own first, then each extra dir; None when none has it."""
    if not re.fullmatch(r"[a-z]{2,3}", code):
        return None
    yaml = require("yaml", "pyyaml")
    for d in (toolkit_dir(), *map(Path, extra_dirs)):
        path = d / f"{code}.yaml"
        if path.is_file():
            try:
                return _build(code, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
            except (OSError, KeyError, TypeError, re.error, yaml.YAMLError):
                return None
    return _build("en", _EN) if code == "en" else None


def code(prd) -> str:
    return prd.frontmatter.get("language") or "en"


def for_prd(prd) -> Table:
    """The PRD's language table, or `en` when `language:` is absent or has no table."""
    return load(code(prd)) or load("en")
