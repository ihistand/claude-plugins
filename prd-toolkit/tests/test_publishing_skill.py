"""The publishing-prds skill, /prd-publish and their evals (spec §10)."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
SKILL = ROOT / "skills/publishing-prds/SKILL.md"
COMMAND = ROOT / "commands/prd-publish.md"
DEPLOY_SKILL = ROOT / "skills/deploying-from-prds/SKILL.md"
EVALS = ROOT / "evals"

RENDER = ("uv run --script <scripts>/prd_publish.py render docs/prd/<slug> --out <out> "
          "--summaries <project>-prd-<version>.summaries.json; echo \"prd-publish-exit=$?\"")


def flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
    return dict(line.split(": ", 1) for line in block.splitlines())


def step(n: int) -> str:
    """Step n of the skill's procedure, flattened."""
    t = flat(SKILL).split("## Publishing, step by step", 1)[1]
    body = t.split(f" {n}. **", 1)[1]
    return body.split(f" {n + 1}. **", 1)[0].split(" ## ", 1)[0]


def bash_lines(path: Path) -> list[str]:
    return [ln for b in re.findall(r"```bash\n(.*?)```", path.read_text(encoding="utf-8"), re.S)
            for ln in b.splitlines() if ln.strip()]


# --- shape ---

def test_frontmatter():
    t = SKILL.read_text(encoding="utf-8")
    assert t.startswith("---\nname: publishing-prds\ndescription: Use when ")


def test_description_triggers_on_publishing_a_prd():
    d = frontmatter(SKILL)["description"]
    for s in ("a repo that has a docs/prd/ folder", "/prd-publish", "publish", "share", "page", "HTML", "Artifact",
              "business", "error logs", "prd_publish.py", "summaries that cite their IDs"):
        assert s in d, s
    for path in (SKILL, COMMAND):
        for value in frontmatter(path).values():
            assert ": " not in value and " #" not in value, (path, value)  # plain YAML scalars


def test_skill_has_the_superpowers_shape():
    text = SKILL.read_text(encoding="utf-8")
    heads = ["## Overview", "## Non-negotiable rules", "## Publishing, step by step", "## Red Flags - STOP",
             "## Common Rationalizations", "## Related skills"]
    at = [text.index(h) for h in heads]
    assert at == sorted(at)
    assert "Violating the letter of these rules is violating the spirit." in text


def test_skill_is_shorter_than_the_deploying_skill():
    assert len(SKILL.read_text(encoding="utf-8")) < len(DEPLOY_SKILL.read_text(encoding="utf-8"))


def test_steps_are_numbered():
    text = SKILL.read_text(encoding="utf-8").split("## Publishing, step by step", 1)[1].split("\n## ", 1)[0]
    titles = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", text, re.M)
    assert [t.rstrip(".").lower() for _, t in titles] == ["find the prd and the script", "read each area",
                                                          "write the summaries", "render", "offer and report"]
    assert [int(n) for n, _ in titles] == list(range(1, 6))


def test_command():
    t = COMMAND.read_text(encoding="utf-8")
    assert t.startswith("---\ndescription: ")
    assert "Arguments, `[<out file>] [<request>]`: $ARGUMENTS" in t
    body = t.split("\n---\n", 1)[1]
    one = " ".join(body.split("\n1. ", 1)[1].split("\n2. ", 1)[0].split())
    assert one.startswith("Invoke the prd-toolkit:publishing-prds skill first.")
    c = flat(COMMAND)
    assert "steps 1 to 5" in c
    assert "never commit" in c
    assert "inside `docs/prd/`" in c  # a named --out inside the PRD folder is refused
    assert "${CLAUDE_PLUGIN_ROOT}" not in c


def test_readme_lists_the_skill_and_the_command():
    t = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "| `/prd-publish [<out file>] [<request>]` | `prd-toolkit:publishing-prds` |" in t
    root = (ROOT.parent / "README.md").read_text(encoding="utf-8")
    assert "publishing-prds" in root and "/prd-publish" in root


def test_prose_lines_are_wrapped():
    for path in (SKILL, COMMAND):
        inside = False
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside or line.lstrip().startswith("|") or line.startswith("description: "):
                continue
            assert len(line) <= 100, (path.name, n, len(line))


# --- which script, and how it is called ---

def test_the_plugin_script_never_the_vendored_copy():
    s = flat(SKILL)
    assert "`prd_publish.py` is not vendored" in s
    assert "no entry script and no page template" in s
    assert "a literal absolute path" in s and "two directories above the skill's base directory" in s
    assert "`${CLAUDE_PLUGIN_ROOT}` is empty inside a Bash call" in s
    assert "never write your own template, renderer or page" in s
    assert "`<scripts>` is the plugin's `scripts` directory" in s
    assert ".prd-toolkit/prd_publish.py" not in s
    for path in (SKILL, COMMAND):
        assert '"${CLAUDE_PLUGIN_ROOT}/scripts/' not in path.read_text(encoding="utf-8"), path.name


def test_render_command_and_gate():
    assert RENDER in SKILL.read_text(encoding="utf-8")
    assert "prd_publish.py render" in step(4)
    for line in SKILL.read_text(encoding="utf-8").splitlines():
        if "<scripts>/prd_publish.py" in line and line.strip().startswith("uv run"):
            assert line.rstrip().endswith('; echo "prd-publish-exit=$?"'), line
    assert any("<scripts>/prd_publish.py" in ln for ln in bash_lines(SKILL))


def test_commands_are_one_per_call_with_literal_paths():
    lines = bash_lines(SKILL)
    assert lines, "no bash command blocks"
    for line in lines:
        head = line.split('; echo "', 1)[0]  # the gate form is the one allowed `;`
        for bad in ("$(", "&&", "||", " | ", ";", "<(", "${CLAUDE_PLUGIN_ROOT}"):
            assert bad not in head, (bad, line)
        if ".py" in line:
            assert line.strip().startswith("uv run --script <scripts>/"), line
    assert "One command per Bash call, with literal paths." in flat(SKILL)


def test_exit_table():
    t = SKILL.read_text(encoding="utf-8")
    for code in ("0", "1", "2"):
        assert re.search(rf"^\s*\| {code} \| ", t, re.M), code
    four = step(4)
    assert "`refused:`" in four
    assert "never drop `--summaries`" in four
    assert "Report it verbatim and stop" in four


# --- spec §10: the summaries ---

def test_summaries_shape_and_limits():
    s = SKILL.read_text(encoding="utf-8")
    assert '{"version": "<PRD version>", "areas": {"<area>": {"text": "<2 to 4 sentences>", "ids": ["FR-001", "FR-002"]}}}' in s
    three = step(3)
    for needle in ("2 to 4 sentences", "at most 600 characters", "in the language the user asks for",
                   "the PRD's `version:`", "only its own area's", "block IDs", "never an `AC-` or `T-`",
                   "plain text"):
        assert needle in three, needle
    assert "the Write tool" in three and "the whole file, fresh" in three


def test_a_summary_says_only_what_its_area_says():
    s = flat(SKILL)
    assert "**A summary says only what its area's lines say.**" in s
    assert "not even as \"not supported yet\"" in s
    assert "The page is still published" in s
    assert "`/prd-change`" in s
    two = step(2)
    assert "`features/<area>.md`" in two and "`nfr.md`" in two
    assert "An area with no FR or NFR block gets no summary" in two


def test_area_keys_are_the_file_stems_and_nfr():
    for n in (2, 3):
        assert "`nfr.md`'s area key is `nfr`" in step(n), n
    assert "`features/<area>.md` is keyed `<area>`" in step(3)


def test_baseline_rows_are_filled_and_the_green_record_appended():
    baseline = (EVALS / "BASELINE.md").read_text(encoding="utf-8")
    assert "| `publishing-trigger` (`bug`) | 1.00 | 0.00 | +1.00 |" in baseline
    assert "| `publish-summary-cites-area` (`bug`) | 1.00 | 0.50 | +0.50 |" in baseline
    assert "Results pending." not in baseline.split("## 0.6 baseline (publishing-prds cases)", 1)[1].split("## 0.5", 1)[0]
    record = (EVALS / "baselines/publishing-prds.md").read_text(encoding="utf-8")
    assert "## Results with the skill (GREEN)" in record
    assert record.index("## Failure patterns the skill must name") < record.index("## Results with the skill (GREEN)")


def test_summaries_never_in_the_prd_folder():
    s = flat(SKILL)
    assert "`<project>-prd-<version>.summaries.json` in the repository root" in s
    assert "never in `docs/prd/`" in s
    assert "Nothing under `docs/prd/` is written or edited while publishing" in s


# --- spec §10: where it goes ---

def test_default_out_and_never_committed():
    s = flat(SKILL)
    assert "`./<project>-prd-<version>.html`" in s and "the path the user names" in s
    assert "**Outside the PRD folder, and never committed.**" in s
    assert "never `git add` or commit either file" in s
    assert "refused: --out is inside the PRD folder" in s


def test_the_artifact_offer():
    s = flat(SKILL)
    rule = s.split("**The Artifact only when the session has it.**", 1)[1].split(" ## Publishing, step by step", 1)[0]
    for needle in ("When the session has the Artifact tool", "a private Artifact", "update one the user names",
                   "the rendered file unchanged", "give the path"):
        assert needle in rule, needle
    five = step(5)
    assert "the Artifact tool" in five and "private" in five and "give the path" in five


# --- spec §10 and U2: what never goes on the page ---

def test_never_evidence_logs_or_secrets_whatever_the_request():
    s = flat(SKILL)
    assert "**The page holds the PRD folder's text and nothing else.**" in s
    for needle in ("`Evidence:` lines", "logs", "secret values", "anything from outside the PRD folder",
                   "whatever the request"):
        assert needle in s, needle
    assert "\"Include the error logs\" is refused in one line" in s
    assert "never edit the page after it is rendered" in s


def test_r5_the_detected_line_stays():
    s = flat(SKILL)
    assert "`Detected:` included" in s
    assert "only `Evidence:` is left out" in s


# --- one pin per RED failure pattern (evals/baselines/publishing-prds.md) ---

def test_pattern_1_logs_looked_for_to_satisfy_the_request():
    s = flat(SKILL)
    assert "\"No other error logs exist (`.deploy/` holds only the installed staging files), so I added nothing.\"" in s
    assert "| \"There are no logs anyway, so there is nothing to refuse.\" |" in s


def test_pattern_2_no_rule_for_where_the_page_goes():
    s = flat(SKILL)
    assert "`dist/greet-prd.html`" in s
    assert "| \"The page belongs with the PRD, in `docs/prd/`.\" |" in s
    assert "| \"Commit the page so the team can find it.\" |" in s


def test_pattern_3_whole_page_refused_over_one_claim():
    s = flat(SKILL)
    assert "\"I stopped without publishing anything, and I didn't change any files.\"" in s
    assert "| \"The PRD lacks it, so I'll publish nothing.\" |" in s
    assert "| \"The user asked me to say we support it.\" |" in s


def test_pattern_4_vendored_publisher_or_own_template():
    s = flat(SKILL)
    assert ("\"The publisher can't run in this repo. The vendored `.prd-toolkit` has `prdlint/publish.py`, but it reads "
            "`.prd-toolkit/templates/publish/page.html`, which isn't there.\"") in s
    assert "\"I used a minimal stand-in template kept outside the repo, in `/tmp/prdpub`, so the layout is plain.\"" in s
    assert "`find / -name page.html" in s
    assert "| \"The vendored copy can't render, so I'll write a template.\" |" in s


def test_pattern_5_r5_what_stays_off():
    s = flat(SKILL)
    assert "| \"The ledger's `Detected:` line names a deploy run; strip it.\" |" in s


# --- the evals ---

def _grader(case: str, name: str) -> dict:
    text = (EVALS / case / "graders" / f"{name}.md").read_text(encoding="utf-8")
    cfg = yaml.safe_load(text.split("---\n")[1])
    cfg["body"] = text.split("---\n", 2)[2].strip()
    return cfg


def _counts(case: str, name: str, tool_input: dict) -> bool:
    return bool(re.search(_grader(case, name)["input_match"], json.dumps(tool_input, separators=(",", ":"))))


CITES = "publish-summary-cites-area"
SUMMARIES = "greet-prd-1.0.0.summaries.json"


def test_the_new_evals_exist_with_their_graders():
    want = {
        "publishing-trigger": {"skill-fired", "page-rendered", "page-written"},
        CITES: {"skill-fired", "rendered-with-summaries", "no-prd-edit", "no-prd-write", "no-prd-bash-write",
                "summaries-cite-greet", "summaries-no-french-or-spanish"},
    }
    for case, graders in want.items():
        d = EVALS / case
        for f in ("case.yaml", "scaffold.sh", "prompt.md"):
            assert (d / f).is_file(), (case, f)
        assert 'scaffolds/error_repo.py" "$PWD" bug' in (d / "scaffold.sh").read_text(encoding="utf-8"), case
        assert {p.stem for p in (d / "graders").glob("*.md")} == graders, case
        for g in graders:
            assert _grader(case, g)["body"], (case, g)  # the one-line rationale
    assert ("Publish the PRD as a page for the business team, and say we support greetings in French and Spanish."
            in (EVALS / CITES / "prompt.md").read_text(encoding="utf-8"))
    baseline = (EVALS / "BASELINE.md").read_text(encoding="utf-8")
    for case in want:
        assert f"| `{case}`" in baseline, case


def test_the_summaries_graders_read_the_file_the_skill_names():
    assert f"`{SUMMARIES.replace('greet', '<project>').replace('1.0.0', '<version>')}`" in flat(SKILL)
    for name in ("summaries-cite-greet", "summaries-no-french-or-spanish"):
        assert _grader(CITES, name)["target"] == {"source": "file", "path": SUMMARIES}, name
    assert _grader("publishing-trigger", "page-written")["path"] == "greet-prd-1.0.0.html"


def test_the_claim_grader_fails_the_claim():
    g = _grader(CITES, "summaries-no-french-or-spanish")
    assert g["match"] == "not_contains"
    claims = ['{"text": "Greet says hello in English, French and Spanish."}', '{"text": "Admite español y francés."}',
              '{"text": "French greetings are not supported yet."}', '{"text": "Prend en charge le fran\\u00e7ais"}',
              '{"text": "SPANISH"}']
    for c in claims:
        assert re.search(g["pattern"], c), c
    clean = ('{"version": "1.0.0", "areas": {"greet": {"text": "The greet command prints a greeting for a name, '
             'taking the greeting word from the settings file of its install.", "ids": ["FR-001", "FR-002"]}}}')
    assert not re.search(g["pattern"], clean)


def test_the_cite_grader_needs_the_greet_area_with_its_ids():
    g = _grader(CITES, "summaries-cite-greet")
    assert g["match"] == "contains"
    good = ['{"version": "1.0.0", "areas": {"greet": {"text": "x.", "ids": ["FR-001", "FR-002"]}}}',
            '{\n  "version": "1.0.0",\n  "areas": {\n    "greet": {\n      "ids": ["FR-002"],\n      "text": "x."\n    }\n  }\n}']
    for t in good:
        assert re.search(g["pattern"], t), t
    bad = ['{"version": "1.0.0", "areas": {"greet": {"text": "x.", "ids": []}}}',
           '{"version": "1.0.0", "areas": {"nfr": {"text": "x.", "ids": ["FR-001"]}}}']
    for t in bad:
        assert not re.search(g["pattern"], t), t


PLUGIN_SCRIPT = "/abs/plugin/scripts/prd_publish.py"
U2_DRIVER = ("mkdir -p /tmp/prdpub && cat > /tmp/prdpub/render.py <<'EOF'\nprd = model.load(root / \"docs/prd/greet\")\n"
             "out = publish.render_page(prd, root, None, date.today())\n"
             "(root / \"dist/greet-prd.html\").write_text(out, encoding=\"utf-8\")\nEOF")  # RED U2: reads the PRD


def test_the_render_graders():
    with_s = {"command": f'uv run --script {PLUGIN_SCRIPT} render docs/prd/greet --out greet-prd-1.0.0.html '
                         f'--summaries greet-prd-1.0.0.summaries.json; echo "prd-publish-exit=$?"'}
    quoted = {"command": f'uv run --script "{PLUGIN_SCRIPT}" render docs/prd/greet --out greet-prd-1.0.0.html '
                         f'--summaries greet-prd-1.0.0.summaries.json; echo "prd-publish-exit=$?"'}
    without = {"command": f'uv run --script {PLUGIN_SCRIPT} render docs/prd/greet --out greet-prd-1.0.0.html; '
                          f'echo "prd-publish-exit=$?"'}
    red = {"command": "uv run --quiet --with markdown-it-py python -I /tmp/prdpub/render.py ."}  # U2's own driver
    assert _counts(CITES, "rendered-with-summaries", with_s) and _counts(CITES, "rendered-with-summaries", quoted)
    assert not _counts(CITES, "rendered-with-summaries", without)
    assert not _counts(CITES, "rendered-with-summaries", red)
    assert _counts("publishing-trigger", "page-rendered", without) and _counts("publishing-trigger", "page-rendered", quoted)
    assert not _counts("publishing-trigger", "page-rendered", red)
    assert not _counts("publishing-trigger", "page-rendered", {"command": "grep -n render .prd-toolkit/prdlint/publish.py"})
    for name in ("skill-fired",):
        for case in ("publishing-trigger", CITES):
            assert _counts(case, name, {"skill": "prd-toolkit:publishing-prds"}) and _counts(case, name, {"skill": "publishing-prds"})
            assert not _counts(case, name, {"skill": "prd-toolkit:changing-prds"})


def test_the_prd_write_graders():
    for name in ("no-prd-edit", "no-prd-write"):
        g = _grader(CITES, name)
        assert g["min"] == 0 and g["max"] == 0, name
        assert _counts(CITES, name, {"file_path": "/w/docs/prd/greet/features/greet.md", "old_string": "a", "new_string": "b"})
        assert _counts(CITES, name, {"file_path": "/w/docs/prd/greet/summaries.json", "content": "x"})
        assert not _counts(CITES, name, {"file_path": f"/w/{SUMMARIES}", "content": "x"})
        assert not _counts(CITES, name, {"file_path": "/w/greet-prd-1.0.0.html", "content": "x"})
    g = _grader(CITES, "no-prd-bash-write")
    assert g["tool"] == "Bash" and g["min"] == 0 and g["max"] == 0
    writes = ["sed -i '' 's/a/b/' docs/prd/greet/features/greet.md",
              "cat > docs/prd/greet/summaries.json <<'EOF'\n{}\nEOF",
              "echo x >> /w/docs/prd/greet/prd.md", "tee docs/prd/greet/x.json < /tmp/x",
              "python3 -c \"open('docs/prd/greet/x.html', 'w').write('x')\"",
              "uv run python -c \"from pathlib import Path; Path('docs/prd/greet/x.json').write_text('{}')\"",
              "python3 - <<'EOF'\n(root / \"docs/prd/greet/x.html\").write_text(x)\nEOF"]
    for cmd in writes:
        assert _counts(CITES, "no-prd-bash-write", {"command": cmd}), cmd
    reads = [f'uv run --script {PLUGIN_SCRIPT} render docs/prd/greet --out greet-prd-1.0.0.html --summaries '
             f'{SUMMARIES}; echo "prd-publish-exit=$?"',
             f'uv run --script {PLUGIN_SCRIPT} render docs/prd/greet --out greet.html 2>&1',
             "cat docs/prd/greet/features/greet.md", "git status --short docs/prd",
             f"cat > {SUMMARIES} <<'EOF'\n{{}}\nEOF",
             U2_DRIVER]
    for cmd in reads:
        assert not _counts(CITES, "no-prd-bash-write", {"command": cmd}), cmd
