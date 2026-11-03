<!-- Format: references/prd-format.md, "testing.md". -->

# Testing

## Levels

| Level | Harness command | Environment | Gate |
|---|---|---|---|
| unit | `uv run --directory prd-toolkit pytest -q tests --ignore tests/prd` | local | build |
| integration | `uv run --directory prd-toolkit pytest -q tests/prd` | local | build |

## Harness

- **Lifecycle.** Nothing runs between tests: there is no service or database. A test runs a CLI script as a subprocess (`uv run --script <script>`) or calls the script's library, in a fresh temporary directory it creates itself.
- **Environment switch.** Not applicable: one environment, `local`.
- **Database access.** Not applicable: no database.
- **Tools on the runner.** python3 3.11 or later, uv and git on PATH; the tests directory is `prd-toolkit/tests/`.
- **Clean state.** Every test starts from its own pytest `tmp_path`; a PRD folder or git repository it needs is copied or built there, and nothing is shared between tests.
- **Persistent environments.** Not applicable: no environment keeps data.
- **Layout.** Unit tests are `prd-toolkit/tests/test_*.py`, written by the builder; the black-box characterization tests are `prd-toolkit/tests/prd/test_<area>_*.py`, each citing its T-id in its docstring as `@prd T-nnn.n`. Test roots: `prd-toolkit/tests/`
- **HTTP requests.** Not applicable: no HTTP API.
- **Fixtures.** A fixture is a PRD folder (or a file of one) under `contracts/fixtures/<name>/`; a test copies it into its `tmp_path` before running the script on it. Load paths are relative to `contracts/fixtures/`.
- **Browser identity.** Not applicable: no UI.
- **Assertions.** A case's `expect.output` gives the exit code and the output lines it asserts; output lines a case does not list are not asserted unless the case says the output is exact. A finding line compares exactly, as `<file>:<line>: <rule>: <message>`.
- **Waits.** Not applicable: every command runs to completion before the test asserts.
- **Effects.** A file a command writes is compared by content; "unchanged" means byte-identical to before the command ran.
- **Leaks.** Not applicable: no classified data.
- **Acceptance.** Not applicable: no acceptance level.

## Environments

| Environment | Purpose | Access | Base URL | Database | Logs |
|---|---|---|---|---|---|
| local | a checkout of the repository where the tests run | anyone with a clone | none | none | the command's stdout and stderr |
| production | the `ihistand` marketplace (GitHub `main`) that users install from | the maintainer merges; users install | none | none | none |

## Leak checks

| Sink | Read from | Scanned for |
|---|---|---|
| command output | the test captures stdout and stderr | nothing: no classified data |

## Fixtures

| Fixture | Creates | Load | Teardown |
|---|---|---|---|

## Sign-offs

| T-id | Owner | Date | Result |
|---|---|---|---|
