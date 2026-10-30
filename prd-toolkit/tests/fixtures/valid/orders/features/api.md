# API

### UJ-01 Rep looks up an order
Status: live (since 1.0.0)
Flow: 1. Rep asks for an order by id → 2. API returns it, or ORDER_NOT_FOUND.
[ASSUMPTION A-01: Reps see only their own orders]
Traces: FR-002, FR-003

### FR-002 Get an order
Status: live (since 1.0.0)
Flow: 1. Caller sends GET /orders/{id} → 2. API checks the role → 3. reads `orders.id`
      → 4a. found: returns it  4b. missing: returns 404
Acceptance (EARS):
- AC-002.1 When a rep requests an existing order through `op:getOrder`, the API shall
  return the order with its status.
- AC-002.2 If the order id does not exist, the API shall respond 404 with error ORDER_NOT_FOUND.
Errors: ORDER_NOT_FOUND (contracts/errors.yaml)
Tests: T-002.1 [integration], T-002.2 [integration]  (test-cases/api.yaml)
Traces: UJ-01; `orders.id`

### FR-003 Delete an order
Status: live (since 1.0.0)
Flow: 1. Caller sends DELETE /orders/{id} → 2. API checks the role
      → 3a. admin: deletes the row  3b. rep: refuses
Acceptance (EARS):
- AC-003.1 When an admin deletes an existing order through `op:deleteOrder`, the API shall
  remove the order and respond 204.
- AC-003.2 If a rep calls `op:deleteOrder`, the API shall respond 403 with error FORBIDDEN
  and keep the order.
Errors: FORBIDDEN (contracts/errors.yaml)
Tests: T-003.1 [integration], T-003.2 [integration]  (test-cases/api.yaml)
Traces: UJ-01; contracts/permissions.yaml
