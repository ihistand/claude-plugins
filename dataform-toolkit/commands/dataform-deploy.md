---
description: Deploy tested Dataform table to production
---

You are deploying a Dataform table to production using best practices from the dataform-engineering-fundamentals skill.

**Workflow:**

1. Invoke the dataform-engineering-fundamentals skill
2. Ask the user which table they want to deploy
3. **Pre-deployment verification:**
   - Confirm the table has been tested in dev environment
   - Verify all tests are passing
   - Check that documentation (columns: {}) is complete
4. **Deployment:**
   - Run `dataform run --dry-run --actions <table_name>` (production dry-run)
   - If successful, run `dataform run --actions <table_name>` (production execution)
   - Verify deployment with validation queries
5. Report deployment results

**Critical**: Never deploy without dev testing first. Wrong results delivered quickly are worse than correct results delivered with a small delay.
