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

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | Developer machine, throwaway database | Developer | http://localhost:8080 | `orders_local` on localhost:5432 | the uvicorn console |
| ci | Pipeline run, fresh database per job | CI service account | http://localhost:8080 | `orders_ci`, created per job | the job log |
| staging | Production-shaped, synthetic data only | Team, test identities | https://orders-staging.example.com | `orders_staging` | `./logs.sh staging` |

## Leak checks

| Sink | Read from | Scanned for |
|---|---|---|
| application logs | the Logs column of the case's environment | `customers.email`, `customers.name` (pii) |
| error bodies | every response body of a case with `expect.errors` | `customers.email`, `customers.name` (pii) |

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
