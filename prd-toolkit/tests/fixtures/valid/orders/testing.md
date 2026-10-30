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

## Harness

- **Lifecycle.** `docker compose up -d db api` starts PostgreSQL and the API before a local or ci run; staging is always running.
- **Environment switch.** `TEST_ENV` is `local`, `ci` or `staging`; the CI job sets `ci`, the staging jobs set `staging`, and it defaults to `local`.
- **Database access.** psycopg through `DATABASE_URL`, which compose and the CI job set; tests never connect to staging's database.
- **Tools on the runner.** The CI image has `psql`, `python3` and Chromium on PATH; `tests/` sits at the repository root.
- **Clean state.** On `local` and `ci`, an autouse fixture in `tests/conftest.py` truncates `orders` and `customers` before every test.
- **Persistent environments.** On `staging`, tests never truncate or load fixtures; the staging deploy job seeds every fixture once, idempotently.
- **Layout.** `tests/<level>/test_<area>.py`, where the area is the feature file's name (`import`, `api`, `nfr`); each test's docstring cites its T-id, e.g. `@prd T-001.2`. Test roots: `tests/`.
- **HTTP requests.** `httpx` through a `client` fixture: the environment's Base URL, `Accept: application/json` by default, and the identity's token from its role's `secret` as a bearer header.
- **Fixtures.** `load_fixture(name)` runs the fixture's Load command from the repository root; an autouse fixture loads a case's preconditions after the clean-state truncate.
- **Browser identity.** Not applicable: the product has no UI.
- **Assertions.** Fields a case does not list are not asserted; a list response asserts its length and order, and each item follows the same rule; content types match on the media type only.
- **Waits.** An expectation waits up to 5 s for a log line before it fails.
- **Effects.** An effect checks only the columns it names; "unchanged" checks every column of the fixture row, after casting the fixture's text to each column's type.
- **Leaks.** After the request, wait 2 s, then read every Leak checks sink and fail on an exact, case-sensitive match of any classified value from the case's input or fixtures.
- **Acceptance.** The signer walks the case's steps on staging and adds a Sign-offs row in a merge request; a case that creates data on staging uses a fresh key on every run.

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
