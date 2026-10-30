# Contract types

What each file under `contracts/` must hold. Every contract has two kinds of requirement:

- **Lint-checked**: `prd_lint.py` rule `contracts-valid` reports a violation when it is missing.
- **Required, not machine-checked**: the spec demands it and the quality checklist
  ([quality-checklist.md](quality-checklist.md)) asks for it, but no script can tell. Author it anyway.

Folder layout, frontmatter and the requirement-block grammar are in [prd-format.md](prd-format.md).
Each example below begins with a `# file: contracts/<name>` line. The test suite writes the example
over the matching fixture file and lints it, so the examples stay valid.

A contract file that cannot be parsed is itself a `contracts-valid` violation, and so is a
duplicate YAML key.

## openapi

`contracts/openapi.yaml`. OpenAPI 3.1, in YAML.

Lint-checked:
- The document passes the OpenAPI schema validator.
- Every operation under `paths` and `webhooks` has an `operationId`.
- `x-prd-ids` is a non-empty list; each item is a defined `UJ-`, `FR-`, `NFR-` or `AC-` id.
- `x-error-codes`, `x-preconditions` and `x-effects` are lists. Write `[]` for none.
- Every response except `204` has a content `example` (or `examples`), or is a `$ref`. Error responses included.

Required, not machine-checked:
- An auth scheme under `components.securitySchemes`, a top-level or per-operation `security`, and the role that may call the operation (in `description`; `permissions.yaml` carries the matrix).
- A fully typed request: required fields, formats, ranges and enums on every parameter and body property.
- A schema and example for every response status the operation can return.
- `x-preconditions` names fixtures from `contracts/fixtures/`. `x-effects` names the tables and events the operation changes, as `table:orders`.
- Idempotency, pagination and rate limits, where they apply.

```yaml
# file: contracts/openapi.yaml
openapi: 3.1.0
info:
  title: Orders API
  version: 1.0.0
  description: Look up orders.
security:
  - bearerAuth: []
paths:
  /orders/{id}:
    parameters:
      - name: id
        in: path
        required: true
        description: Order id.
        schema: {type: integer, format: int64, minimum: 1}
    get:
      operationId: getOrder
      summary: Get an order
      description: Roles admin and rep. A rep sees only own orders. Read-only, so safe to retry.
      x-prd-ids: [FR-002, AC-002.1, AC-002.2]
      x-error-codes: [ORDER_NOT_FOUND]
      x-preconditions: [orders/one_existing, customers/two_customers]
      x-effects: []
      responses:
        "200":
          description: The order.
          content:
            application/json:
              schema: {$ref: "#/components/schemas/Order"}
              example: {id: 1, order_key: K-1000, customer_id: 1, status: open}
        "404":
          description: No such order. Error ORDER_NOT_FOUND.
          content:
            application/json:
              schema: {$ref: "#/components/schemas/Error"}
              example: {code: ORDER_NOT_FOUND, message: Order not found}
components:
  securitySchemes:
    bearerAuth: {type: http, scheme: bearer}
  schemas:
    Order:
      type: object
      required: [id, order_key, customer_id, status]
      properties:
        id: {type: integer, format: int64}
        order_key: {type: string, minLength: 1}
        customer_id: {type: integer, format: int64}
        status: {type: string, enum: [open, shipped, cancelled]}
    Error:
      type: object
      required: [code, message]
      properties:
        code: {type: string}
        message: {type: string}
```

## schema

`contracts/schema.sql`. DDL in the dialect named by `sql-dialect` in the `prd.md` frontmatter.

Lint-checked:
- The file parses in that dialect.
- Every `CREATE TABLE` has a `COMMENT ON TABLE` (or `OPTIONS(description=...)`).
- Every column has a `COMMENT ON COLUMN` (or `OPTIONS(description=...)`).

Required, not machine-checked:
- Every column states its type, nullability (`NOT NULL` or nullable on purpose) and default.
- Primary, foreign, unique and check constraints.
- Each comment says what the value means, not the column name again.

```sql
-- file: contracts/schema.sql
CREATE TABLE orders (
  id bigint PRIMARY KEY,
  order_key text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'shipped', 'cancelled'))
);

COMMENT ON TABLE orders IS 'One row per imported order.';
COMMENT ON COLUMN orders.id IS 'Surrogate key.';
COMMENT ON COLUMN orders.order_key IS 'Natural key from the warehouse file; unique.';
COMMENT ON COLUMN orders.status IS 'open, shipped or cancelled.';
```

## events

`contracts/events.md` for jobs and events, or `contracts/asyncapi.yaml` for message brokers.

Lint-checked, `events.md`: each `### <name>` heading has a line starting with each of `Trigger:`,
`Payload:`, `Delivery:`, `Retries:` and `Failure:`. Test cases resolve `event:` and `job:` targets to these headings.

Lint-checked, `asyncapi.yaml`: the file has a top-level `asyncapi` key.

Required, not machine-checked:
- `Trigger:` names the event or the schedule.
- `Payload:` gives the schema and one example.
- `Delivery:` states the guarantee (at least once, at most once) and the ordering.
- `Retries:` gives attempts, spacing and the idempotency key.
- `Failure:` says what happens after the last retry, including dead-letter handling and who is told.

```markdown
<!-- file: contracts/events.md -->
# Events and jobs

### import_orders
Trigger: a file arrives in the staging bucket, or an operator starts the job by hand.
Payload: `{"file": "<bucket path>", "rows": [{"order_key": "K-3000", "customer_id": 1, "status": "open"}]}`
Delivery: at least once; ordering is not guaranteed between files, rows keep file order.
Retries: 3 attempts, 30 s apart; the idempotency key is order_key, so a retry skips rows already stored.
Failure: after 3 failed attempts the file moves to the dead-letter folder and the owner is paged.
```

## errors

`contracts/errors.yaml`. One entry per error code. Codes are `UPPER_SNAKE_CASE`.

Lint-checked:
- The key matches `^[A-Z][A-Z0-9_]*$`.
- Each entry has `meaning`, `when`, `status`, `message`, `log_level`, `retryable` and `metric`.
- `status` is an integer (an HTTP status or an exit code; `0` for a non-fatal outcome).
- `retryable` is `true` or `false`.
- Separate rules (`error-codes`) require every cited code to be catalogued and every catalogued code to be cited somewhere.

Required, not machine-checked:
- `message` is what the user sees, and a person could act on it. See the checklist.
- `metric` names a counter the code increments, and `nfr.md` Observability ties it to a log field and an alert.

```yaml
# file: contracts/errors.yaml
ORDER_NOT_FOUND:
  meaning: No order has the requested id.
  when: getOrder receives an id that is not in orders.
  status: 404
  message: Order not found
  log_level: info
  retryable: false
  metric: orders_not_found_total
```

## permissions

`contracts/permissions.yaml`. A role by operation matrix, row rules, and a test identity and its
secret per role.

Lint-checked:
- `roles` maps each role to a mapping with a non-empty `identity`.
- `operations` maps each operation to `{allow: [...], deny: [...]}`, both lists.
- Every role appears in exactly one of `allow` and `deny`. No unknown roles.
- `row_rules`, if present, is a list of mappings with `role`, `operation`, `predicate` and `attribute`.
- The test-case rule `deny-tested` requires a test for every deny cell: a test case with
  `target: op:<operation>`, `identity:` set to the denied role's test identity, and a non-empty
  `expect.errors` (the code the denial returns, such as `FORBIDDEN`).

Required, not machine-checked:
- Each role's `secret` names the secret that holds its test identity's credential (a token or
  password), as listed in `operations.md` Secrets. It is a name, never a value.
- `predicate` reads as a condition on a named user attribute (`orders.sales_rep_name = user.sales_rep_name`).
- Every allow cell has a test too. Lint enforces the deny cells only.

```yaml
# file: contracts/permissions.yaml
roles:
  admin: {identity: test-admin, secret: ORDERS_TEST_ADMIN_TOKEN}
  rep: {identity: test-rep, secret: ORDERS_TEST_REP_TOKEN}
operations:
  getOrder: {allow: [admin, rep], deny: []}
  deleteOrder: {allow: [admin], deny: [rep]}
row_rules:
  - role: rep
    operation: getOrder
    predicate: "orders.sales_rep_name = user.sales_rep_name"
    attribute: sales_rep_name
```

## config

`contracts/config.yaml`. One entry per setting and feature flag.

Lint-checked:
- `settings` is a mapping from name to a mapping with `type`, `default`, `environments` and `owner`.
- `environments` is a mapping from environment name to value.

Required, not machine-checked:
- `environments` names every environment in `testing.md`.
- `owner` says who may change the value.

```yaml
# file: contracts/config.yaml
settings:
  IMPORT_BATCH_SIZE:
    type: integer
    default: 500
    environments: {local: 10, ci: 10, staging: 500, production: 500}
    owner: Sample Owner
```

## classification

`contracts/data-classification.yaml`. Sensitivity per column, retention and masking.

Lint-checked:
- `tables` maps each table to a mapping with `retention`, `deletion` and `columns`.
- Each column's class is `public`, `internal`, `confidential` or `pii`.
- `masking` has `logs`, `errors` and `fixtures`.
- Separate rules (`classified-fixtures` and others) check test fixtures against these classes.

Required, not machine-checked:
- Every column in `schema.sql` is classified.
- Fixtures hold synthetic PII only; `masking.fixtures` says how values are made synthetic.

```yaml
# file: contracts/data-classification.yaml
tables:
  customers:
    retention: 7 years after the last order
    deletion: anonymize email and name within 30 days of a request
    columns: {id: internal, email: pii, name: pii}
masking:
  logs: customer email and name never logged; log the customer id instead
  errors: error bodies carry a code and a fixed message only
  fixtures: synthetic values only; emails use the example.com domain
```

## dependencies

`contracts/dependencies/<service>.yaml`. One file per third-party service.

Lint-checked:
- Keys `sends`, `expects`, `auth`, `limits`, `mock` and `failures` are present.
- `auth` is a mapping with `secret`.
- `failures` is a mapping with `timeout`, `4xx`, `5xx` and `outage`. Each value is an error code, and the `error-codes` rule checks it is catalogued.

Required, not machine-checked:
- `sends` and `expects` each carry an example.
- `auth.secret` names the secret, never its value.
- `mock` names the sandbox or recorded-response mock that tests use. Tests never call a production third party.

```yaml
# file: contracts/dependencies/geocoder.yaml
sends:
  description: One postal code per call.
  example: {postal_code: "12345", country: US}
expects:
  description: A latitude and longitude, or a not-found flag.
  example: {found: true, lat: 40.0, lon: -75.0}
auth:
  secret: GEOCODER_API_KEY
limits: 50 requests/s, 100000 requests per day
mock: tests/mocks/geocoder.py replays recorded answers; tests never call the live service
failures:
  timeout: GEOCODER_TIMEOUT
  4xx: GEOCODER_TIMEOUT
  5xx: GEOCODER_TIMEOUT
  outage: GEOCODER_TIMEOUT
```

## fixtures

`contracts/fixtures/<table>/<name>.csv` (or `.yaml` or `.json` as `{table: [rows]}`). Lint checks
fixture contents, not their shape: the `classified-fixtures` rule fails on real-looking PII, and
`test-refs` fails when a test case names a fixture that does not exist. A fixture name is its path
without the extension, such as `orders/one_existing`.

Required, not machine-checked:
- `testing.md` has a Fixtures row per dataset: the state it creates and the load and teardown commands.
- The state it creates is stated in plain words, so a tester can predict results without opening the file.

## components

UI component contracts live in `prd.md` §10, not under `contracts/`. Lint does not check them.

Required, not machine-checked, per component:
- Name and typed inputs.
- Every state: loading, empty, error and populated.
- Events emitted.
- Test hooks, as `data-testid` names.
- Accessibility rules (labels, focus order, keyboard use).

## custom

A custom type is a row in `prd.md` §7 whose validator is not `built-in`:

| Type | Files (glob) | Validator |
|---|---|---|
| lookml | `contracts/custom/*.lkml` | `python3 -c "import sys; sys.exit(0)"` |

Lint-checked: the validator command runs with the matching files appended as arguments, from the
PRD root. Exit 0 passes. Any other exit, a missing command or a run over `PRD_VALIDATOR_TIMEOUT`
seconds (default 120) is a `contracts-valid` violation. A row whose glob matches no file is skipped.
A custom type's name is also a legal `target` kind in test cases.

Required, not machine-checked: the type defines a format, a validator that fails on a real defect
(prove it can fail), and how each item supplies the seven sufficiency elements. Example: a Looker
type covers explores, fields with their SQL, dashboards with tiles and filters, and user attributes.

## Observability

Observability lives in `nfr.md`, not in a contract file: log fields, metric names and alert
thresholds, each tied to error codes. An error the system cannot surface is an error EDD cannot catch.
