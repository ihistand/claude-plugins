# Import

### FR-001 Import an orders file
Status: live (since 1.0.0)
Flow: 1. Importer reads a file → 2. validates each row's postal code with the geocoder
      → 3. looks up orders.order_key → 4a. new: inserts  4b. exists: skips and logs
Acceptance (EARS):
- AC-001.1 When an imported row has a new order_key, the importer shall insert the row
  into `orders`.
- AC-001.2 When an imported row's order_key already exists, the importer shall skip the row
  and log `IMPORT_DUPLICATE` once for it.
- AC-001.3 If the import file is empty, the importer shall finish with status `empty`,
  log `IMPORT_EMPTY` and insert no rows.
Errors: IMPORT_DUPLICATE, IMPORT_EMPTY (contracts/errors.yaml)
Edge cases: the same key twice in one file → AC-001.2
Tests: T-001.1 [integration], T-001.2 [integration], T-001.3 [unit], T-001.4 [acceptance]  (test-cases/import.yaml)
Traces: `orders.order_key` UNIQUE; fixtures orders/one_existing, customers/two_customers
