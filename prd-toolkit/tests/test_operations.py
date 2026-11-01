"""The operations.md model (Operations, Step) and the runbook-steps rule."""
from conftest import edit, lint

from prdlint import model


def msgs(prd):
    return {(f.rule, f.message) for f in lint(prd)}


def test_fixture_steps(prd):
    ops = model.load(prd).operations
    assert [(s.number, s.actor, s.env) for s in ops.steps] == [
        (1, "agent", "staging"), (2, "agent", "staging"), (3, "human", "production"),
        (4, "agent", "production"), (5, "agent", "production")]
    s1, s2 = ops.steps[0], ops.steps[1]
    assert s1.run == "./deploy.sh staging" and s1.check == "curl -fsS https://orders-staging.example.com/health" and s1.prints == "ok"
    assert s1.rollback == "./deploy.sh staging --previous" and s2.tests == ["system", "e2e"] and s2.check is None
    assert model.production_envs(model.load(prd)) == {"production"}
    assert ops.secrets == ["GEOCODER_API_KEY", "ORDERS_TEST_ADMIN_TOKEN", "ORDERS_TEST_REP_TOKEN"]
    assert ops.has_production and ops.production["staging"] == "no" and "staging" in ops.environments


def test_absent_operations_is_empty(prd):
    (prd / "operations.md").unlink()
    ops = model.load(prd).operations
    assert ops.steps == [] and not ops.has_production and model.production_envs(model.load(prd)) == set()


def test_fixture_is_clean(prd):
    assert not [m for m in msgs(prd) if m[0] == "runbook-steps"]


def test_step_without_env(prd):
    edit(prd, "operations.md", "(actor: agent) (env: staging)\n   Run: `./deploy.sh staging`", "(actor: agent)\n   Run: `./deploy.sh staging`")
    assert ("runbook-steps", "step 1: the step line needs (actor: agent|human) (env: <environment>)") in msgs(prd)


def test_agent_step_needs_check(prd):
    edit(prd, "operations.md", "   Check: `curl -fsS https://orders-staging.example.com/health` prints `ok`\n", "")
    assert ("runbook-steps", "step 1: an agent step needs Check:") in msgs(prd)


def test_human_step_labels(prd):
    edit(prd, "operations.md", '   Do: read the staging results', '   Run: `./go.sh`\n   Do: read the staging results')
    assert ("runbook-steps", "step 3: a human step takes Do: and Check:, not Run:") in msgs(prd)


def test_command_not_backticked(prd):
    edit(prd, "operations.md", "Run: `./deploy.sh staging`\n", "Run: ./deploy.sh staging\n")
    m = [x for r, x in msgs(prd) if r == "runbook-steps" and x.startswith("step 1: Run: must be one backticked command or tests <level>")]
    assert m


def test_tests_step_takes_no_check(prd):
    edit(prd, "operations.md", "   Run: tests system, e2e\n", "   Run: tests system, e2e\n   Check: `true`\n")
    assert ("runbook-steps", "step 2: a tests step has no Check:") in msgs(prd)


def test_numbering_gap(prd):
    edit(prd, "operations.md", "3. Approve production", "4. Approve production")
    assert ("runbook-steps", "step 4: expected step 3") in msgs(prd)


def test_old_runbook_names_the_migration(prd):
    p = prd / "operations.md"
    text = p.read_text()
    head, rest = text.split("## Runbook\n")
    _, tail = rest.split("## Secrets")
    p.write_text(head + "## Runbook\n\n1. Deploy with `./deploy.sh staging`. (actor: agent)\n2. Deploy to production. (actor: human)\n\n## Secrets" + tail)
    fs = [f for f in lint(prd) if f.rule == "runbook-steps"]
    assert len(fs) >= 2 and fs[0].message.endswith("(prd-toolkit 0.5 runbook format)")
    assert not fs[1].message.endswith("(prd-toolkit 0.5 runbook format)")


DEPLOYED_DRIFT = """
## Deployed

| Environment | PRD version | Commit | Date | Run |
|---|---|---|---|---|
| staging | 1.0.0 | 3f2c1a9 | 2026-11-02 | 20261102T101500Z-staging |

## Drift

| Environment | Check | Introspection command |
|---|---|---|
| production | version | `./app --prd-version` |
| production | config | none |
"""


def test_deployed_and_drift_rows(prd):
    p = prd / "operations.md"
    before = p.read_text()
    head, rest = before.split("## Deployed")  # drop the fixture's own tables
    p.write_text(head + DEPLOYED_DRIFT.lstrip("\n") + "\n## Secrets" + rest.split("## Secrets")[1])
    ops = model.load(prd).operations
    ln = lambda needle: next(i for i, t in enumerate(p.read_text().split("\n"), 1) if needle in t)
    (d,) = ops.deployed
    assert (d.env, d.version, d.commit, d.date, d.run) == ("staging", "1.0.0", "3f2c1a9", "2026-11-02", "20261102T101500Z-staging")
    assert d.line == ln("| staging | 1.0.0")
    v, c = ops.drift
    assert (v.env, v.check, v.command, v.line) == ("production", "version", "./app --prd-version", ln("| production | version"))
    assert (c.env, c.check, c.command, c.line) == ("production", "config", None, ln("| production | config"))


def test_human_step_missing_do(prd):
    edit(prd, "operations.md", '   Do: read the staging results and reply "deploy production"\n', "")
    assert ("runbook-steps", "step 3: a human step needs Do: and Check:") in msgs(prd)


def test_tests_step_may_roll_back(prd):
    edit(prd, "operations.md", "   Run: tests system, e2e\n", "   Run: tests system, e2e\n   Rollback: `./deploy.sh staging --previous`\n")
    assert not [m for m in msgs(prd) if m[0] == "runbook-steps"]


# --- runbook-env, production-gate, runbook-tests, drift-rows, unclassified ---

def test_fixture_drift_and_deployed(prd):
    ops = model.load(prd).operations
    assert [(d.env, d.check) for d in ops.drift] == [("production", "version"), ("production", "config")]
    assert all(d.command for d in ops.drift) and [(d.env, d.version) for d in ops.deployed] == [("production", "1.0.0")]
    assert not {"runbook-env", "production-gate", "runbook-tests", "drift-rows"} & {r for r, _ in msgs(prd)}


def test_env_missing_from_testing(prd):
    edit(prd, "testing.md", "| production | Live service", "| prod | Live service")
    assert ("runbook-env", "environment 'production' is in operations.md but not in testing.md Environments") in msgs(prd)


def test_env_case_differs(prd):
    edit(prd, "operations.md", "(env: staging)\n   Run: `./deploy.sh staging`", "(env: Staging)\n   Run: `./deploy.sh staging`")
    assert ("runbook-env", "step 1: environment 'Staging' is not in operations.md Environments (did you mean 'staging'?)") in msgs(prd)


def test_env_unknown_no_suggestion(prd):
    edit(prd, "operations.md", "(env: staging)\n   Run: `./deploy.sh staging`", "(env: qa)\n   Run: `./deploy.sh staging`")
    assert ("runbook-env", "step 1: environment 'qa' is not in operations.md Environments") in msgs(prd)


def test_empty_env_reported(prd):
    edit(prd, "operations.md", "(env: staging)\n   Run: `./deploy.sh staging`", "(env: )\n   Run: `./deploy.sh staging`")
    assert ("runbook-env", "step 1: environment '' is not in operations.md Environments") in msgs(prd)


def test_backticked_env_matches(prd):
    edit(prd, "operations.md", "(env: staging)\n   Run: `./deploy.sh staging`", "(env: `staging`)\n   Run: `./deploy.sh staging`")
    assert not [m for m in msgs(prd) if m[0] == "runbook-env"]


def test_deployed_and_drift_envs(prd):
    edit(prd, "operations.md", "| production | 1.0.0 |", "| prod | 1.0.0 |")
    edit(prd, "operations.md", "| production | version |", "| Production | version |")
    m = msgs(prd)
    assert ("runbook-env", "Deployed row: environment 'prod' is not in operations.md Environments") in m
    assert ("runbook-env", "Drift row: environment 'Production' is not in operations.md Environments (did you mean 'production'?)") in m


def test_step_env_not_in_testing(prd):
    edit(prd, "testing.md", "| production | Live service", "| prod | Live service")
    assert ("runbook-env", "step 3: environment 'production' is not in testing.md Environments") in msgs(prd)


def test_production_value(prd):
    edit(prd, "operations.md", "| staging | https://orders-staging.example.com | no |", "| staging | https://orders-staging.example.com | maybe |")
    assert ("runbook-env", "environment 'staging': Production 'maybe' is not yes or no") in msgs(prd)


def test_production_value_case_sensitive(prd):
    edit(prd, "operations.md", "| https://orders.example.com | yes |", "| https://orders.example.com | Yes |")
    m = msgs(prd)
    assert ("runbook-env", "environment 'production': Production 'Yes' is not yes or no") in m
    assert ("runbook-env", "operations.md Environments: no environment has Production yes") in m


def test_no_production_row(prd):
    edit(prd, "operations.md", "| https://orders.example.com | yes |", "| https://orders.example.com | no |")
    assert ("runbook-env", "operations.md Environments: no environment has Production yes") in msgs(prd)


def test_no_production_column(prd):
    edit(prd, "operations.md", "| Environment | URL | Production |\n|---|---|---|", "| Environment | URL |\n|---|---|")
    assert [m for m in msgs(prd) if m[0] == "runbook-env" and "no Production column" in m[1]]


def swap_steps_3_and_4(prd):
    text = (prd / "operations.md").read_text()
    head, rest = text.split("3. Approve production", 1)
    approve, rest = rest.split("4. Deploy to production", 1)
    deploy, tail = rest.split("5. Smoke on production", 1)
    (prd / "operations.md").write_text(head + "3. Deploy to production" + deploy + "4. Approve production" + approve + "5. Smoke on production" + tail)


def test_production_gate(prd):
    swap_steps_3_and_4(prd)
    m = msgs(prd)
    assert ("production-gate", "step 3 deploys production with no human step at or just before it") in m
    assert len([x for x in m if x[0] == "production-gate"]) == 1


def test_production_gate_human_first_is_fine(prd):
    assert not [m for m in msgs(prd) if m[0] == "production-gate"]


def test_runbook_tests_level(prd):
    edit(prd, "operations.md", "Run: tests system, e2e", "Run: tests system, nope")
    assert ("runbook-tests", "step 2: level 'nope' is not in testing.md Levels") in msgs(prd)


def test_runbook_tests_gate(prd):
    edit(prd, "operations.md", "Run: tests system, e2e", "Run: tests unit")
    assert ("runbook-tests", "step 2: level 'unit' has Gate build; a tests step runs deploy-gate levels") in msgs(prd)


def test_runbook_tests_command(prd):
    edit(prd, "testing.md", "| e2e | `pytest tests/e2e` |", "| e2e | pytest tests/e2e |")
    assert ("runbook-tests", "step 2: level 'e2e' has no Harness command") in msgs(prd)


def test_drift_schema_row(prd):
    edit(prd, "operations.md", "| production | config | `curl -fsS https://orders.example.com/settings` |",
         "| production | config | `curl -fsS https://orders.example.com/settings` |\n| production | schema | `true` |")
    assert ("drift-rows", "check 'schema': schema drift arrives in prd-toolkit 0.6") in msgs(prd)


def test_drift_unknown_check(prd):
    edit(prd, "operations.md", "| production | version |", "| production | vers |")
    assert ("drift-rows", "check 'vers' is not version or config") in msgs(prd)


def test_drift_config_needs_contract(prd):
    (prd / "contracts/config.yaml").unlink()
    assert ("drift-rows", "a config drift row needs contracts/config.yaml") in msgs(prd)


def test_unclassified_only_open(prd):
    edit(prd, "errors.md", "Classification: code bug", "Classification: unclassified")
    assert ("index-consistent", "E-001: unclassified is allowed only on an open entry") in msgs(prd)


def test_unclassified_open_is_fine(prd):
    edit(prd, "errors.md", "Classification: code bug", "Classification: unclassified")
    edit(prd, "errors.md", "Resolution: the importer returns status `empty` before reading rows; T-001.3 passes", "Resolution: -")
    assert not [m for m in msgs(prd) if "unclassified" in m[1]]


def test_tests_step_rollback_shape(prd):
    edit(prd, "operations.md", "   Run: tests system, e2e\n", "   Run: tests system, e2e\n   Rollback: undo it\n")
    assert ("runbook-steps", "step 2: Rollback: must be one backticked command; got 'undo it'") in msgs(prd)


def test_production_envs_exact_yes(prd):
    edit(prd, "operations.md", "| https://orders.example.com | yes |", "| https://orders.example.com | YES |")
    assert model.production_envs(model.load(prd)) == set()
