# Testing

## Levels

| Level | Harness command | Environment |
|---|---|---|
| unit | `pytest tests/unit` | local |
| integration | `pytest tests/integration` | ci |
| component | `pytest tests/component` | ci |
| system | `pytest tests/system` | staging |
| e2e | `pytest tests/e2e` | staging |
| acceptance | `python3 tools/acceptance_report.py` | staging |

## Environments

| Environment | Purpose | Access |
|---|---|---|
| local | Developer machine, throwaway database | Developer |
| ci | Pipeline run, fresh database per job | CI service account |
| staging | Production-shaped, synthetic data only | Team, test identities |

## Fixtures

| Fixture | Creates | Load | Teardown |
|---|---|---|---|
| orders/one_existing | One order, K-1000, owned by rep-a | `python3 tools/fixture.py load orders/one_existing` | `python3 tools/fixture.py drop orders/one_existing` |
| orders/dup_key_in_file | An import file with the key K-2000 on two rows | `python3 tools/fixture.py load orders/dup_key_in_file` | `python3 tools/fixture.py drop orders/dup_key_in_file` |
| customers/two_customers | Two customers, ids 1 and 2 | `python3 tools/fixture.py load customers/two_customers` | `python3 tools/fixture.py drop customers/two_customers` |

## Sign-offs

| T-id | Owner | Date | Result |
|---|---|---|---|
| T-001.4 | Sample Owner | 2026-10-29 | pass |
