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
