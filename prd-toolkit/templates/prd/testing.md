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
