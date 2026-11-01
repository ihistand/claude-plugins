"""error-entries: the format of an errors.md entry's Detected, Confirmed, Evidence, Recurrence and class lines."""
import re

from ..findings import Finding
from ..model import CLASSES, Prd
from ..registry import rule

MAX_EVIDENCE = 20
_DETECTED = re.compile(r"^\d{4}-\d{2}-\d{2},\s+\S")


@rule("error-entries")
def error_entries(prd: Prd):
    for e in prd.errors_ledger.values():
        def f(line: int, msg: str) -> Finding:
            return Finding("errors.md", line, "error-entries", f"{e.id}: {msg}")

        if e.detected_line and not _DETECTED.match(e.detected):
            yield f(e.detected_line, 'Detected: must be "<YYYY-MM-DD>, <source>"')
        if e.classification and e.classification not in CLASSES:
            yield f(e.classification_line, f"Classification: '{e.classification}' is not one of {', '.join(CLASSES)}")
        if e.confirmed_raw is not None:
            if e.confirmed is None:
                yield f(e.confirmed_line, "Confirmed: must be '<YYYY-MM-DD>, \"<reply>\"'")
            if e.classification in ("", "unclassified"):
                yield f(e.confirmed_line, "Confirmed: on an unclassified entry")
        if len(e.evidence) > MAX_EVIDENCE:
            yield f(e.evidence_line, f"Evidence: is {len(e.evidence)} lines; at most {MAX_EVIDENCE}")
        if e.recurrence and e.recurrence != "-":
            for ref in (t.strip() for t in e.recurrence.split(",")):
                if ref not in prd.errors_ledger:
                    yield f(e.recurrence_line, f"Recurrence of: {ref} is not an entry")

