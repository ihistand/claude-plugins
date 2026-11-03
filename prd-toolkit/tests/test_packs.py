"""Target profiles, the pack manifest, resolution and the pack-resolves rule (0.8.0)."""
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import edit
from packs_fixture import plugins_file, write_pack

from prdlint import languages, model, packs, registry
from prdlint.model import PackRef, Target

S1_ANCHOR = "- Not used: message brokers, ORMs, front-end frameworks"
SERVICE_DEFAULT = PackRef("service", None, "prd-toolkit", "", 0)
TOOLKIT_PACKS = Path(packs.__file__).resolve().parents[2] / "packs"


@pytest.fixture(autouse=True)
def toolkit_080(monkeypatch):
    """The toolkit is 0.7.2 until the release task; the range tests run as 0.8.0."""
    monkeypatch.setattr(packs, "toolkit_version", lambda: "0.8.0")


def _s1(prd, *lines):
    edit(prd, "prd.md", S1_ANCHOR, "\n".join((S1_ANCHOR, *lines)))


def _line(prd, rel, text):
    return (prd / rel).read_text().split("\n").index(text) + 1


def _target(prd, area, line, title=None):
    title = title or {"import": "# Import", "api": "# API"}[area]
    edit(prd, f"features/{area}.md", title + "\n", f"{title}\n\n{line}\n")


def _found(prd):
    return [str(f) for f in registry.run(model.load(prd), only={"pack-resolves"})]


def _demo_plugin(tmp_path, monkeypatch, version="1.0.0", **keys):
    """Install plugin demo@test under a path with a space, holding prd-packs/demo/; return the install path."""
    install = tmp_path / "My Plugins/demo"
    write_pack(install / "prd-packs", "demo", version, description="Demo pack.", **keys)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@test": install})))
    return install


def _git_init(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)


# --- parsing -------------------------------------------------------------------------------------------------------

def test_good_section_1_pair(prd):
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)", "- Output language: es")
    n = _line(prd, "prd.md", "- Pack: demo 1.0.0 (demo@test)")
    p = model.load(prd)
    assert p.pack_ref == PackRef("demo", "1.0.0", "demo@test", "prd.md", n)
    assert p.output_language == ("es", n + 1)
    assert p.profile_problems == []
    assert packs.profile(p, None) == (p.pack_ref, "es")


def test_no_lines_is_the_service_default(prd):
    p = model.load(prd)
    assert (p.pack_ref, p.output_language, p.targets, p.profile_problems) == (None, None, {}, [])
    assert packs.profile(p, None) == (SERVICE_DEFAULT, "en")
    assert packs.profile(p, "import") == (SERVICE_DEFAULT, "en")
    assert packs.named(p) == []


def test_repeated_pack_line(prd):
    _s1(prd, "- Pack: service 1.0.0 (prd-toolkit)", "- Pack: service 1.0.0 (prd-toolkit)")
    first = _line(prd, "prd.md", "- Pack: service 1.0.0 (prd-toolkit)")
    p = model.load(prd)
    assert p.pack_ref.line == first
    assert [(f, n) for f, n, _ in p.profile_problems] == [("prd.md", first + 1)]
    assert [m for _, _, m in p.profile_problems] == [f"Pack: repeated (first at line {first}); one Pack: line per PRD"]


def test_malformed_pack_line(prd):
    _s1(prd, "- Pack: document 1.0")
    n = _line(prd, "prd.md", "- Pack: document 1.0")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: Pack: must be <name> <X.Y.Z> (<source>)"]
    assert model.load(prd).pack_ref is None


@pytest.mark.parametrize("value", ["document 1.0.0", "Document 1.0.0 (prd-toolkit)", "document 1.0.0 (nowhere)"])
def test_other_malformed_pack_lines(prd, value):
    _s1(prd, f"- Pack: {value}")
    assert [m for _, _, m in model.load(prd).profile_problems] == ["Pack: must be <name> <X.Y.Z> (<source>)"]


def test_malformed_and_repeated_output_language(prd):
    _s1(prd, "- Output language: es", "- Output language: Spanish")
    n = _line(prd, "prd.md", "- Output language: es")
    p = model.load(prd)
    assert p.output_language == ("es", n)
    assert p.profile_problems == [
        ("prd.md", n + 1, f"Output language: repeated (first at line {n}); one Output language: line per PRD"),
    ]
    edit(prd, "prd.md", "- Output language: es\n", "")
    p = model.load(prd)
    assert p.output_language is None
    assert p.profile_problems == [("prd.md", n, "Output language: must be a BCP 47 tag such as es or pt-BR")]


def test_target_above_the_heading_is_reported(prd):
    path = prd / "features/import.md"
    path.write_text("Target: output language es\n\n" + path.read_text())
    assert _found(prd) == ["features/import.md:1: pack-resolves: Target: must come after the file's level-1 heading"]


def test_target_with_both_parts(prd):
    _target(prd, "import", "Target: pack demo 1.0.0 (demo@test), output language pt-BR")
    p = model.load(prd)
    assert p.targets == {"import": Target("import", "features/import.md", 3, PackRef("demo", "1.0.0", "demo@test", "features/import.md", 3), "pt-BR")}
    assert p.profile_problems == []
    assert packs.profile(p, "import") == (p.targets["import"].pack, "pt-BR")
    assert packs.profile(p, "api") == (SERVICE_DEFAULT, "en")


def test_target_with_one_part_inherits_the_other(prd):
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)", "- Output language: es")
    _target(prd, "import", "Target: output language pt-BR")
    _target(prd, "api", "Target: pack document 1.0.0 (prd-toolkit)")
    p = model.load(prd)
    assert p.targets["import"].pack is None and p.targets["import"].output_language == "pt-BR"
    assert packs.profile(p, "import") == (p.pack_ref, "pt-BR")
    assert packs.profile(p, "api") == (p.targets["api"].pack, "es")
    assert [r.name for r in packs.named(p)] == ["demo", "document"]


def test_target_output_language_falls_back_to_prd_language(prd):
    edit(prd, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: es")
    assert packs.profile(model.load(prd), "import") == (SERVICE_DEFAULT, "es")


@pytest.mark.parametrize("line", ["Target:", "Target: nothing here", "Target: pack document 1.0", "Target: output language en, pack document 1.0.0 (prd-toolkit)"])
def test_target_with_neither_part_is_a_finding(prd, line):
    _target(prd, "import", line)
    assert _found(prd) == ["features/import.md:3: pack-resolves: Target: must be pack <name> <X.Y.Z> (<source>)[, output language <code>] or output language <code>"]
    assert model.load(prd).targets == {}


def test_target_below_the_heading_and_a_comment_resolves(prd):
    path = prd / "features/import.md"
    text = path.read_text()
    assert text.startswith("# Import\n\n### FR-001")
    path.write_text('<!-- Format: references/prd-format.md, "Requirement blocks".\nTarget: output language fr -->\n\n'
                    "# Import\n\n<!--\nTarget: output language de\n-->\n\nTarget: output language es\n\n" + text[len("# Import\n\n"):])
    p = model.load(prd)
    assert p.profile_problems == []
    assert p.targets["import"].line == 10 and p.targets["import"].output_language == "es"


def test_target_in_a_code_fence_is_not_read(prd):
    _target(prd, "import", "```\nTarget: output language es\n```")
    p = model.load(prd)
    assert p.targets == {} and p.profile_problems == []


def test_target_after_a_requirement_is_reported(prd):
    edit(prd, "features/import.md", "Status: live (since 1.0.0)\n", "Status: live (since 1.0.0)\nTarget: output language es\n")
    n = _line(prd, "features/import.md", "Target: output language es")
    assert _found(prd) == [f"features/import.md:{n}: pack-resolves: Target: must come before the first requirement"]
    assert model.load(prd).targets == {}


def test_repeated_target_line(prd):
    _target(prd, "import", "Target: output language es\nTarget: output language pt-BR")
    p = model.load(prd)
    assert p.targets["import"].output_language == "es"
    assert p.profile_problems == [("features/import.md", 4, "Target: repeated (first at line 3); one Target: line per area")]


def test_nfr_blocks_take_section_1(prd):
    _s1(prd, "- Output language: es")
    assert packs.profile(model.load(prd), None)[1] == "es"


# --- resolution ----------------------------------------------------------------------------------------------------

def test_builtin_found(prd):
    _s1(prd, "- Pack: service 1.0.0 (prd-toolkit)")
    assert _found(prd) == []
    pack = packs.pack_for(model.load(prd), None)
    assert (pack.name, pack.version, pack.source, pack.root) == ("service", "1.0.0", "prd-toolkit", TOOLKIT_PACKS / "service")


def test_service_default_resolves_unlocked(prd):
    pack = packs.pack_for(model.load(prd), "import")
    assert (pack.name, pack.source) == ("service", "prd-toolkit")


def test_service_manifest_holds_the_spec_values():
    pack = packs.load_manifest(TOOLKIT_PACKS / "service", "prd-toolkit")
    assert [c["type"] for c in pack.contract_types] == ["openapi", "schema", "events", "errors", "permissions", "config",
                                                         "classification", "dependencies", "fixtures"]
    assert {c["validator"] for c in pack.contract_types} == {"built-in"}
    assert (pack.target_kinds, pack.levels, pack.harness, pack.vocabulary, pack.builder_tests) == ({}, [], {}, [], "unit")
    assert packs.in_range("0.7.2", pack.data["toolkit"]) and packs.in_range("0.8.9", pack.data["toolkit"])


def test_plugin_pack_found_through_the_plugins_file(prd, tmp_path, monkeypatch):
    install = _demo_plugin(tmp_path, monkeypatch)
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    assert _found(prd) == []
    pack = packs.pack_for(model.load(prd), "import")
    assert (pack.name, pack.version, pack.source, pack.root) == ("demo", "1.0.0", "demo@test", install / "prd-packs/demo")


def test_plugin_pack_not_found_names_only_the_plugin(prd, tmp_path, monkeypatch):
    """R13: a plugin source looks in that plugin only; no .prd-toolkit/, so no vendored place."""
    install = tmp_path / "My Plugins/demo"
    install.mkdir(parents=True)
    monkeypatch.setenv("PRD_PLUGINS_FILE", str(plugins_file(tmp_path, {"demo@test": install})))
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    n = _line(prd, "prd.md", "- Pack: demo 1.0.0 (demo@test)")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: pack demo 1.0.0 (demo@test) not found; looked in: "
                           f"{install}/prd-packs/demo/"]
    assert packs.pack_for(model.load(prd), None) is None


def test_pack_not_found_when_the_plugin_is_not_installed(prd):
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    with pytest.raises(packs.PackNotFound) as e:
        packs.resolve(model.load(prd).pack_ref, prd)
    assert e.value.looked == ["plugin demo@test (not installed)"]


def test_vendored_place_listed_only_when_the_repo_vendors(prd, tmp_path):
    _git_init(tmp_path)
    (tmp_path / ".prd-toolkit").mkdir()
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    with pytest.raises(packs.PackNotFound) as e:
        packs.resolve(model.load(prd).pack_ref, tmp_path)
    assert e.value.looked == [f"{tmp_path}/.prd-toolkit/packs/demo/", "plugin demo@test (not installed)"]


def test_a_plugin_source_never_resolves_to_a_builtin(prd, tmp_path):
    """R13: `service 1.0.0 (demo@test)` is not the built-in service, and its source is never rewritten."""
    _s1(prd, "- Pack: service 1.0.0 (demo@test)")
    with pytest.raises(packs.PackNotFound) as e:
        packs.resolve(model.load(prd).pack_ref, tmp_path)
    assert e.value.looked == ["plugin demo@test (not installed)"]
    n = _line(prd, "prd.md", "- Pack: service 1.0.0 (demo@test)")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: pack service 1.0.0 (demo@test) not found; looked in: "
                           "plugin demo@test (not installed)"]


def test_a_builtin_source_never_consults_plugins(prd, tmp_path, monkeypatch):
    install = _demo_plugin(tmp_path, monkeypatch)
    ref = PackRef("demo", "1.0.0", "prd-toolkit", "prd.md", 1)
    with pytest.raises(packs.PackNotFound) as e:
        packs.resolve(ref, tmp_path)
    assert e.value.looked == [f"{TOOLKIT_PACKS}/demo/"]
    assert (install / "prd-packs/demo/pack.yaml").is_file()


def test_pack_at_another_version_is_not_a_hit(prd, tmp_path, monkeypatch):
    install = _demo_plugin(tmp_path, monkeypatch, version="1.0.0")
    _s1(prd, "- Pack: demo 1.1.0 (demo@test)")
    (msg,) = _found(prd)
    assert msg.endswith(f"pack demo 1.1.0 (demo@test) not found; looked in: {install}/prd-packs/demo/ (holds 1.0.0)")


def test_vendored_version_differs(prd, tmp_path, monkeypatch):
    _git_init(tmp_path)
    write_pack(tmp_path / ".prd-toolkit/packs", "demo", "1.0.0")
    _demo_plugin(tmp_path, monkeypatch, version="1.1.0")  # vendored is the only candidate once vendored
    _s1(prd, "- Pack: demo 1.1.0 (demo@test)")
    n = _line(prd, "prd.md", "- Pack: demo 1.1.0 (demo@test)")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: vendored demo 1.0.0, the PRD names 1.1.0; run prd_hooks.py install"]
    with pytest.raises(packs.PackMismatch) as e:
        packs.resolve(model.load(prd).pack_ref, tmp_path)
    assert (e.value.vendored, e.value.named) == ("1.0.0", "1.1.0")
    assert packs.resolve(model.load(prd).pack_ref, tmp_path, vendored=False).version == "1.1.0"


def test_vendored_copy_resolves(prd, tmp_path):
    _git_init(tmp_path)
    folder = write_pack(tmp_path / ".prd-toolkit/packs", "demo", "1.0.0")
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    assert _found(prd) == []
    assert packs.pack_for(model.load(prd), None).root == folder


def test_two_versions_across_targets(prd):
    _target(prd, "api", "Target: pack document 1.0.0 (prd-toolkit)")
    _target(prd, "import", "Target: pack document 1.1.0 (prd-toolkit)")
    assert "features/import.md:3: pack-resolves: pack document named at 1.0.0 and 1.1.0; one version per PRD" in _found(prd)
    assert not any("1.1.0 (prd-toolkit) not found" in m for m in _found(prd))


def test_toolkit_range_excludes_this_toolkit(prd, tmp_path, monkeypatch):
    _demo_plugin(tmp_path, monkeypatch, toolkit=">=0.9")
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    n = _line(prd, "prd.md", "- Pack: demo 1.0.0 (demo@test)")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: pack demo needs toolkit >=0.9; this is 0.8.0"]


@pytest.mark.parametrize("keys,key,message", [
    ({"version": None}, "version", "pack demo: pack.yaml: version is required"),
    ({"toolkit": None}, "toolkit", "pack demo: pack.yaml: toolkit is required"),
    ({"version": "1.0"}, "version", "pack demo: pack.yaml: version must be X.Y.Z"),
    ({"levels": {}}, "levels", "pack demo: pack.yaml: levels must be a list"),
    ({"vocabulary": "explore"}, "vocabulary", "pack demo: pack.yaml: vocabulary must be a list"),
    ({"harness": []}, "harness", "pack demo: pack.yaml: harness must be a mapping"),
    ({"harness": {"Lunch": "x"}}, "harness", "pack demo: pack.yaml: harness: 'Lunch' is not a Harness slot"),
    ({"builder_tests": "some"}, "builder-tests", "pack demo: pack.yaml: builder-tests must be unit or none"),
    ({"pack": "other"}, "pack", "pack demo: pack.yaml: pack must equal the folder name demo"),
    ({"toolkit": "about 0.8"}, "toolkit", "pack demo: pack.yaml: toolkit must be a version range such as >=0.8.0,<0.9"),
    ({"colour": "blue"}, "colour", "pack demo: pack.yaml: unknown key colour"),
    ({"contract_types": [{"type": "outline"}]}, "contract-types", "pack demo: pack.yaml: contract-types[0] must be a mapping with type, files and validator"),
    ({"target_kinds": {"doc": "outline"}}, "target-kinds", "pack demo: pack.yaml: target-kinds: doc maps to outline, not a contract type of this pack"),
    ({"rubrics": "rubrics.md"}, "rubrics", "pack demo: pack.yaml: rubrics: rubrics.md is not a file in the pack"),
    ({"contract_types": [{"type": "outline", "files": "contracts/outline.yaml", "validator": "built-in"}]}, "contract-types",
     "pack demo: only the service pack may use validator built-in"),
])
def test_manifest_errors(tmp_path, keys, key, message):
    version = keys.pop("version", "1.0.0")
    folder = write_pack(tmp_path, "demo", version, **keys)
    with pytest.raises(packs.ManifestError) as e:
        packs.load_manifest(folder, "demo@test")
    assert (str(e.value), e.value.key) == (message, key)


def test_manifest_error_is_a_finding(prd, tmp_path, monkeypatch):
    _demo_plugin(tmp_path, monkeypatch, levels={})
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    n = _line(prd, "prd.md", "- Pack: demo 1.0.0 (demo@test)")
    assert _found(prd) == [f"prd.md:{n}: pack-resolves: pack demo: pack.yaml: levels must be a list"]


def test_full_manifest_properties(tmp_path):
    folder = write_pack(tmp_path, "demo", "1.0.0", description="Demo pack.",
                        contract_types=[{"type": "outline", "files": "contracts/outline.yaml", "validator": "uv run --script ${PACK}/v.py"}],
                        target_kinds={"doc": "outline"}, levels=[{"level": "checks", "command": "uv run pytest", "environment": "local", "gate": "build"}],
                        harness={"Lifecycle": "Not applicable: none"}, standards=[], skills=[], vocabulary=["explore", "data tile"],
                        builder_tests="none", rubrics="rubrics.md", clarify="clarify.md", grader="uv run --script ${PACK}/grade.py",
                        languages="languages/")
    for name in ("rubrics.md", "clarify.md"):
        (folder / name).write_text("x\n")
    (folder / "languages").mkdir()
    pack = packs.load_manifest(folder, "demo@test")
    assert pack.target_kinds == {"doc": "outline"} and pack.vocabulary == ["explore", "data tile"]
    assert (pack.builder_tests, pack.description, pack.grader) == ("none", "Demo pack.", "uv run --script ${PACK}/grade.py")
    assert (pack.rubrics, pack.clarify, pack.languages_dir) == (folder / "rubrics.md", folder / "clarify.md", folder / "languages")
    assert pack.levels[0]["level"] == "checks" and pack.harness == {"Lifecycle": "Not applicable: none"}
    assert pack.standards == [] and pack.skills == []


def test_a_07_vendored_repo_with_no_pack_line_is_unchanged(prd, tmp_path):
    """Review Focus 1: .prd-toolkit/ from 0.7 (no packs/) and no Pack: line give no finding and the same lint output."""
    before = registry.run(model.load(prd), warnings=True)
    _git_init(tmp_path)
    (tmp_path / ".prd-toolkit").mkdir()
    (tmp_path / ".prd-toolkit/VERSION").write_text("0.7.1\n")
    p = model.load(prd)
    assert registry.run(p, only={"pack-resolves"}) == []
    assert registry.run(p, warnings=True) == before


# --- toolkit version and ranges ------------------------------------------------------------------------------------

@pytest.mark.parametrize("version,spec,expected", [
    ("0.8.0", ">=0.8.0,<0.9", True),
    ("0.8.5", ">=0.8.0,<0.9", True),
    ("0.9.0", ">=0.8.0,<0.9", False),
    ("0.7.2", ">=0.8.0,<0.9", False),
    ("0.8.0", ">=0.9", False),
    ("0.9.0", ">=0.9", True),
    ("0.8.0", ">0.8.0", False),
    ("0.8.1", ">0.8", True),
    ("0.8.0", "<=0.8.0", True),
    ("0.8.1", "<=0.8.0", False),
    ("0.8.0", "==0.8.0", True),
    ("0.8.0", "==0.8", True),
    ("0.8.1", "==0.8.0", False),
    ("0.8.0", "!=0.8.0", False),
    ("0.8.1", "!=0.8.0", True),
    ("0.8.0", " >= 0.8.0 , < 0.9 ", True),
    ("1.0.0", ">=0.8.0,!=1.0.0", False),
])
def test_in_range(version, spec, expected):
    assert packs.in_range(version, spec) is expected


@pytest.mark.parametrize("spec", ["", "0.8.0", "~=0.8", ">=0.8.*", ">=0.8,", "=>0.8"])
def test_in_range_rejects_a_bad_specifier(spec):
    with pytest.raises(ValueError):
        packs.in_range("0.8.0", spec)


def test_toolkit_version_reads_the_plugin_manifest(monkeypatch):
    monkeypatch.undo()
    import json
    assert packs.toolkit_version() == json.loads((TOOLKIT_PACKS.parent / ".claude-plugin/plugin.json").read_text())["version"]


# --- expand, discover, --list-packs, languages --------------------------------------------------------------------

def test_expand_keeps_a_spaced_pack_path_one_argument(tmp_path):
    """Review Focus 2: ${PACK} is substituted per argument after shlex.split."""
    folder = write_pack(tmp_path / "My Packs", "demo", "1.0.0")
    (folder / "ok.py").write_text("import sys\nsys.exit(0 if sys.argv[1:] == ['--flag'] else 3)\n")
    pack = packs.load_manifest(folder, "demo@test")
    argv = packs.expand('python3 "${PACK}/ok.py" --flag', pack)
    assert argv == ["python3", f"{folder}/ok.py", "--flag"]
    argv2 = packs.expand("python3 ${PACK}/ok.py --flag", pack)
    assert argv2 == argv
    assert subprocess.run([sys.executable, *argv[1:]]).returncode == 0


def test_discover_skips_a_bad_manifest(tmp_path, monkeypatch, capsys):
    install = _demo_plugin(tmp_path, monkeypatch)
    write_pack(install / "prd-packs", "broken", None)
    found = packs.discover()
    assert [(p.name, p.source) for p in found][-1] == ("demo", "demo@test")
    assert "broken" not in [p.name for p in found]
    assert "pack broken: pack.yaml: version is required" in capsys.readouterr().err


def test_list_packs_prints_builtins_then_plugins(tmp_path, monkeypatch, capsys):
    from prd_lint import main

    _demo_plugin(tmp_path, monkeypatch)
    assert main(["--list-packs"]) == 0
    lines = capsys.readouterr().out.splitlines()
    builtins = sorted(d.name for d in TOOLKIT_PACKS.iterdir() if (d / "pack.yaml").is_file())
    assert "service" in builtins
    assert [line.split()[0] for line in lines] == builtins + ["demo"]
    service = packs.load_manifest(TOOLKIT_PACKS / "service", "prd-toolkit")
    assert f"service 1.0.0 (prd-toolkit) — {service.description}" in lines
    assert lines[-1] == "demo 1.0.0 (demo@test) — Demo pack."


def test_a_named_packs_language_table_is_used(prd, tmp_path, monkeypatch):
    install = _demo_plugin(tmp_path, monkeypatch, languages="languages/")
    tables = install / "prd-packs/demo/languages"
    tables.mkdir()
    en = (TOOLKIT_PACKS.parent / "references/languages/en.yaml").read_text()
    (tables / "fr.yaml").write_text(en.replace("language: en", "language: fr"))
    edit(prd, "prd.md", "sql-dialect: postgres", "sql-dialect: postgres\nlanguage: fr")
    assert [f.message for f in registry.run(model.load(prd), only={"language-table"})] == ["language 'fr' has no table"]
    _s1(prd, "- Pack: demo 1.0.0 (demo@test)")
    p = model.load(prd)
    assert registry.run(p, only={"language-table", "pack-resolves"}) == []
    assert languages.for_prd(p).code == "fr"
