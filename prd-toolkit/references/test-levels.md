# Test levels

The six levels a test case can carry in `level:`. A level must be a row of the Levels table in
`testing.md`, or lint rule `test-level` fires. Case fields are in [prd-format.md](prd-format.md).

| Level | Written from | Owner | Reads code? | Runs |
|---|---|---|---|---|
| unit | the builder's own design | builder | yes | CI, milliseconds |
| integration | `contracts/` | tester | no | CI, against a real database and services in containers, dependency mocks |
| component | component contracts (`prd.md` §10) | tester | no | CI |
| system | FRs and NFRs, in a production-like environment | tester | no | staging |
| e2e | user journeys (`UJ-nn`) | tester | no | staging; a smoke subset on production |
| acceptance | EARS criteria and the Definition of Done | tester writes scripts from `steps:`; people sign | no | staging; sign-off recorded in `testing.md` |

The tester never sees the code, so its tests check the build independently.

## Fields each level emphasises

Every case carries the sufficiency fields (`ac`, `level`, `target`, `environment`, `identity`,
`preconditions`, `input`, `expect`). The table shows what each level leans on.

| Level | Emphasis |
|---|---|
| unit | `target: code:<function>` (unit level only); `environment: local`; `preconditions` often empty; exact `expect.output` |
| integration | `target: op:`, `table:`, `event:` or `job:`; `preconditions` name fixtures and `mock:<service>`; `expect.effects` and `expect.errors`; `identity` for permission cases |
| component | `target: component:<name>`; `input` sets the component state; `expect.output` is what renders, found by `data-testid` |
| system | `target` is a job or operation; `environment` names an environment other than `local`; `expect` carries NFR numbers |
| e2e | `target: page:<name>` or `job:<name>`; `ac` points at the AC a journey step proves; `identity` is a real role's test identity |
| acceptance | adds `steps:` and `signoff:`; written in the owner's words |

Rules:

- Acceptance carries `steps` (a non-empty list of plain-language actions) and `signoff` (the business owner). Lint rule `sufficiency` fails without them.
- A system case names an environment other than `local`. This is required, not machine-checked: lint accepts any environment from `testing.md`.
- Tests never call production third parties. Use `mock:<service>`.
- `expect.leaks: none` means no classified column named in `testing.md` Leak checks appears in
  any sink that table lists (logs and error bodies at least). Keep it on every case.
