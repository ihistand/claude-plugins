# Events and jobs

### import_orders
Trigger: a file arrives in the staging bucket, or an operator starts the job by hand.
Payload: `{"file": "<bucket path>", "rows": [{"order_key": "K-3000", "customer_id": 1, "status": "open", "sales_rep_name": "rep-a"}]}`; the example above carries one row.
Delivery: at least once; ordering is not guaranteed between files, rows keep file order.
Retries: 3 attempts, 30 s apart; the idempotency key is order_key, so a retry skips rows already stored.
Failure: after 3 failed attempts the file moves to the dead-letter folder and the owner is paged.
