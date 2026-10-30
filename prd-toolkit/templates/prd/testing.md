<!-- Format: references/prd-format.md, "testing.md". -->

# Testing

## Levels

| Level | Harness command | Environment |
|---|---|---|
| unit | [NEEDS CLARIFICATION: unit harness command] | [NEEDS CLARIFICATION: environment] |
| integration | [NEEDS CLARIFICATION: integration harness command] | [NEEDS CLARIFICATION: environment] |
| component | [NEEDS CLARIFICATION: component harness command] | [NEEDS CLARIFICATION: environment] |
| system | [NEEDS CLARIFICATION: system harness command] | [NEEDS CLARIFICATION: environment] |
| e2e | [NEEDS CLARIFICATION: e2e harness command] | [NEEDS CLARIFICATION: environment] |
| acceptance | [NEEDS CLARIFICATION: acceptance harness command] | [NEEDS CLARIFICATION: environment] |

## Harness

<!--
The conventions every test relies on. A black-box tester reads only this folder, so each one
must be written here before any test case is. State the convention, not a helper's code: how a
helper is built inside (method signatures, return values, defaults) is the tester's choice and
goes in its HARNESS CHOICES. Answer a slot that does not apply with `Not applicable: <reason>`,
for example Browser identity when there is no UI.
-->

- **Lifecycle.** [NEEDS CLARIFICATION: who starts the system and its database before a test run (the harness, a compose file, the CI job), and how]
- **Environment switch.** [NEEDS CLARIFICATION: how a test knows which environment it runs in (a variable and its values), and the default]
- **Database access.** [NEEDS CLARIFICATION: how a test reads and writes the database: the client library and the variable holding the connection]
- **Tools on the runner.** [NEEDS CLARIFICATION: which command-line tools the runner has on PATH (database client, load tool, browser), and where the tests directory sits]
- **Clean state.** [NEEDS CLARIFICATION: on which environments every test starts from empty tables, which tables, and who empties them]
- **Persistent environments.** [NEEDS CLARIFICATION: on environments that keep data (staging), how fixtures get there (seeded once, idempotently) and what tests must never do there]
- **Layout.** [NEEDS CLARIFICATION: where each level's tests live and how files are named, including non-Python scripts, and how a test cites its T-id]. Test roots: [NEEDS CLARIFICATION: the test directories, each in backticks]
- **HTTP requests.** [NEEDS CLARIFICATION: the HTTP library tests use, its base URL and default headers (Accept), and how a test acts as each identity]
- **Fixtures.** [NEEDS CLARIFICATION: the fixture-loading helper, and how a case's preconditions are loaded before the test body; what Load paths are relative to]
- **Browser identity.** [NEEDS CLARIFICATION: the browser-test plugin and base URL, and how a browser test acts as each identity; or Not applicable: no UI]
- **Assertions.** [NEEDS CLARIFICATION: whether fields a case does not list are asserted, how list responses and their items compare, how text and content types match, and what "above" means on a page]
- **Waits.** [NEEDS CLARIFICATION: how long an expectation waits for an element, a state or a log line before it fails, unless the case says otherwise]
- **Effects.** [NEEDS CLARIFICATION: which columns an effect checks, what "unchanged" compares, and how fixture text compares to typed columns]
- **Leaks.** [NEEDS CLARIFICATION: which values a leak check scans for, how they match (exact, case), how long to wait for logs, and how logs are read on each environment]
- **Acceptance.** [NEEDS CLARIFICATION: how a signer runs an acceptance case and records the result, and how a case on a persistent environment uses fresh data on every run]

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| [NEEDS CLARIFICATION: first environment] | [NEEDS CLARIFICATION: purpose] | [NEEDS CLARIFICATION: who may use it] | [NEEDS CLARIFICATION: base URL a test calls, or none] | [NEEDS CLARIFICATION: database or connection a test uses, never a password] | [NEEDS CLARIFICATION: where this environment's logs are read] |

## Leak checks

| Sink | Read from | Scanned for |
|---|---|---|
| application logs | [NEEDS CLARIFICATION: how a test reads the logs] | [NEEDS CLARIFICATION: classified columns from contracts/data-classification.yaml that must never appear] |
| error bodies | [NEEDS CLARIFICATION: which responses or outputs carry error bodies] | [NEEDS CLARIFICATION: classified columns that must never appear] |

## Fixtures

| Fixture | Creates | Load | Teardown |
|---|---|---|---|
| [NEEDS CLARIFICATION: first fixture name, a path under contracts/fixtures/ without extension] | [NEEDS CLARIFICATION: what it creates] | [NEEDS CLARIFICATION: load command] | [NEEDS CLARIFICATION: teardown command] |

## Sign-offs

| T-id | Owner | Date | Result |
|---|---|---|---|
