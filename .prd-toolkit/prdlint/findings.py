from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Finding:
    """One violation. `file` is relative to the PRD root; `line` is 1-based, 0 for a whole file."""

    file: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.rule}: {self.message}"
