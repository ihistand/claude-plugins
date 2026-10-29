from prdlint.registry import RULES

SPEC_RULES = {"frontmatter","sections","id-format","id-unique","id-removed-reused","index-consistent",
  "fr-has-ac","ac-has-test","ac-ears","test-cases-consistent","test-level","sufficiency","test-refs",
  "nfr-bound","deny-tested","error-codes","classified-fixtures","markers-open","assumption-indexed",
  "placeholder","vague-word","glossary-synonym","contracts-valid","schema-refs","registries",
  "runbook-actors","open-questions-empty"}


def test_rule_set_matches_spec():
    import prdlint.rules  # noqa: F401  registers every rule

    assert set(RULES) == SPEC_RULES


def test_every_rule_has_a_failing_case():
    import test_rules_structure as a, test_rules_ids as b, test_rules_testcases as c
    import test_rules_contracts as d, test_rules_registries as e
    covered = {case.rule for m in (a, b, c, d, e) for case in m.CASES}
    assert covered == SPEC_RULES
