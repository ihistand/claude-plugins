---
description: Create new Dataform table using TDD workflow
---

You are creating a new Dataform table following the Test-Driven Development (TDD) workflow from the dataform-engineering-fundamentals skill.

**Workflow:**

1. Invoke the dataform-engineering-fundamentals skill
2. Ask the user about the table requirements:
   - Table name and purpose
   - Expected columns and their descriptions
   - Data sources (for creating source declarations if needed)
   - Business logic and transformations
3. **RED Phase - Write tests first:**
   - Create assertion file in `definitions/assertions/`
   - Write data quality tests (duplicates, nulls, invalid values)
   - Run tests - they should FAIL (table doesn't exist yet)
4. **GREEN Phase - Write minimal implementation:**
   - Create source declarations if needed
   - Create table SQLX file with:
     - Proper config block with type, schema
     - Complete columns: {} documentation
     - SQL transformation
   - Run table creation: `dataform run --schema-suffix dev --actions <table_name>`
   - Run tests - they should PASS
5. **REFACTOR Phase - Improve while keeping tests passing:**
   - Optimize query performance if needed
   - Add partitioning/clustering if appropriate
   - Improve documentation clarity
6. Report completion with file locations and next steps

**Critical**: Always write tests FIRST, then implementation. Tests-after means you're checking what it does, not defining what it should do.
