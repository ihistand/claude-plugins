"""Pack rules (0.8.0): pack-resolves."""
from .. import packs
from ..findings import Finding
from ..model import Prd, repo_root
from ..registry import rule


@rule("pack-resolves")
def pack_resolves(prd: Prd):
    """Malformed, repeated or misplaced profile lines, then each named pack that does not resolve, on the line naming it."""
    for file, line, message in prd.profile_problems:
        yield Finding(file, line, "pack-resolves", message)
    refs = packs.named(prd)
    versions: dict[str, list[str]] = {}
    for ref in refs:
        versions.setdefault(ref.name, [])
        if ref.version not in versions[ref.name]:
            versions[ref.name].append(ref.version)
    reported: set[str] = set()
    root = repo_root(prd.root) if refs else None
    for ref in refs:
        first = versions[ref.name][0]
        if ref.version != first:
            if ref.name not in reported:
                reported.add(ref.name)
                vs = versions[ref.name]
                listed = ", ".join(vs[:-1]) + " and " + vs[-1]
                yield Finding(ref.file, ref.line, "pack-resolves", f"pack {ref.name} named at {listed}; one version per PRD")
            continue
        try:
            packs.resolve(ref, root)
        except (packs.ManifestError, packs.PackNotFound, packs.PackMismatch) as e:
            yield Finding(ref.file, ref.line, "pack-resolves", str(e))
        except (OSError, ValueError) as e:
            yield Finding(ref.file, ref.line, "pack-resolves", f"pack {ref.name}: {packs.MANIFEST}: {e}")
