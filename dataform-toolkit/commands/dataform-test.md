---
description: Test Dataform table in dev environment with safety checks
---

You are testing a Dataform table using best practices from the dataform-engineering-fundamentals skill.

**Workflow:**

1. Invoke the dataform-engineering-fundamentals skill
2. Ask the user which table they want to test
3. Follow the safety checklist:
   - Run `dataform compile` to check syntax
   - Run `dataform run --schema-suffix dev --dry-run --actions <table_name>` to validate SQL
   - Run `dataform run --schema-suffix dev --actions <table_name>` to execute in dev
   - Run basic validation queries to verify results
4. Report results and any issues found

**Critical**: Always use `--schema-suffix dev` for testing. Never test directly in production.
