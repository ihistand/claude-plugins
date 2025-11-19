---
name: acuantia-dataform
description: Use when working on Acuantia's BigQuery Dataform pipeline (acuantia-gcp-dataform project) - adds Acuantia-specific patterns on top of dataform-engineering-fundamentals: ODS two-arg ref() syntax, looker_ filename prefix, Looker integration (looker_prod/looker_dev), acuantia dataset conventions, coordination with callrail_data_export/dialpad_data_integration/looker projects
---

# Acuantia Dataform Engineering

## REQUIRED PREREQUISITE

**YOU MUST USE `dataform-engineering-fundamentals` SKILL FIRST.**

This skill is a **thin extension layer** that adds Acuantia-specific patterns on top of the generic `dataform-engineering-fundamentals` skill.

**Before using this skill:**
1. Read and follow `dataform-engineering-fundamentals` completely
2. Apply ALL generic Dataform practices from that skill
3. Then apply the Acuantia-specific patterns below

**This skill does NOT repeat generic practices.** If you're looking for:
- TDD workflow → See `dataform-engineering-fundamentals`
- Safety practices (--schema-suffix dev, --dry-run) → See `dataform-engineering-fundamentals`
- ${ref()} enforcement → See `dataform-engineering-fundamentals`
- Documentation standards → See `dataform-engineering-fundamentals`
- Architecture patterns → See `dataform-engineering-fundamentals`

**This skill ONLY adds**: Acuantia-specific conventions that differ from or extend generic patterns.

## When to Use

Use this skill when working on:
- `acuantia-gcp-dataform` project
- Tables that integrate with Acuantia's Looker instance
- Transformations using Acuantia's ODS (Operational Data Store) architecture
- Pipelines coordinating with `callrail_data_export` or `dialpad_data_integration` projects

## Acuantia-Specific Patterns

### 1. ODS Architecture and Two-Argument ref()

Acuantia uses a special ODS (Operational Data Store) architecture that requires two-argument ref() syntax.

**ODS Architecture**:
- `acuantia.ods` - Source of truth (master operational data)
- `acuantia.ods_dev` - Development/staging dataset
- `acuantia.ods_prod` - Production staging dataset

**CRITICAL**: Use two-argument ref() for ODS tables to avoid suffix duplication:

```sql
-- CORRECT: Two-argument ref() for ODS
FROM ${ref("ods", "sap_customers")}
FROM ${ref("ods", "magento_orders")}

-- WRONG: Single-argument causes ods_dev_dev with --schema-suffix dev
FROM ${ref("sap_customers")}  -- Creates ods_dev_dev ❌
```

**Why**: The ODS schema name itself gets the suffix applied. Two-argument ref() prevents `ods_dev_dev` when using `--schema-suffix dev`.

**All other tables**: Use single-argument ref() as per `dataform-engineering-fundamentals`.

### 2. Looker Table Naming Convention and Layering Architecture

**CRITICAL WORKFLOW**: All Looker tables follow a mandatory two-layer architecture:
- `definitions/intermediate/looker/` - Views with business logic (prefix: `vw_looker*`)
- `definitions/output/looker/` - Tables that materialize the views (prefix: `looker*`)

**REQUIRED PATTERN**:
1. Create intermediate view in `definitions/intermediate/looker/` with `vw_looker*` prefix
2. Create output table in `definitions/output/looker/` with `looker*` prefix (matching view name without `vw_` prefix)
3. Output table MUST be type "table" (never "view") and source from the intermediate view

**File naming convention**:
```
# CORRECT - Two-layer pattern
definitions/intermediate/looker/vw_looker_customer_metrics.sqlx  (view with logic)
definitions/output/looker/looker_customer_metrics.sqlx           (table from view)

definitions/intermediate/looker/vw_looker_sales_summary.sqlx     (view with logic)
definitions/output/looker/looker_sales_summary.sqlx              (table from view)

# WRONG - Table directly in output without intermediate view
definitions/output/looker/looker_customer_metrics.sqlx           ❌
definitions/output/looker/customer_metrics.sqlx                  ❌ (also missing prefix)

# WRONG - Using "view" type in output folder
definitions/output/looker/looker_sales_summary.sqlx              ❌ (if type: "view")
```

**Implementation pattern**:
```sql
-- definitions/intermediate/looker/vw_looker_customer_metrics.sqlx
config {
  type: "view",
  schema: "dataform",  // Intermediate views live in dataform schema
  description: "Customer metrics calculation logic",
  columns: {
    customer_id: "Unique customer identifier",
    lifetime_value: "Total customer lifetime value",
    order_count: "Total number of orders"
  }
}

SELECT
  customer_id,
  SUM(order_total) as lifetime_value,
  COUNT(DISTINCT order_id) as order_count
FROM ${ref("ods", "orders")}
GROUP BY customer_id

-- definitions/output/looker/looker_customer_metrics.sqlx
config {
  type: "table",  // MUST be "table", never "view"
  schema: "looker",  // Base name - suffix appended automatically
  tags: ["looker", "daily"],
  columns: {
    customer_id: "Unique customer identifier",
    lifetime_value: "Total customer lifetime value",
    order_count: "Total number of orders"
  }
}

SELECT * FROM ${ref("vw_looker_customer_metrics")}
```

**Why this layering pattern**:
- Separates business logic (intermediate views) from materialization (output tables)
- Intermediate views can be modified and tested without recreating Looker tables
- Multiple output tables can reference the same intermediate logic
- Clear naming convention makes the view-to-table relationship obvious
- Makes Looker-specific tables immediately identifiable
- Prevents naming conflicts with other intermediate tables
- Aligns with Looker project conventions in `looker/` directory

**Schema configuration requirements**:
- Intermediate views: `schema: "dataform"` (base name, suffix is appended)
- Output tables: `schema: "looker"` (base name, NOT `"looker_prod"` - suffix is appended automatically)
  - With `--schema-suffix dev` → `looker_dev`
  - With `--schema-suffix prod` → `looker_prod`

**Config name convention**:
- **DO NOT include `name:` in config if it matches the filename**
- Dataform automatically uses the filename (without .sqlx) as the table/view name
- Only specify `name:` when it must differ from the filename (e.g., for deduplication or dependency reasons)

```sql
-- WRONG: Redundant name specification
-- File: looker_customer_metrics.sqlx
config {
  type: "table",
  name: "looker_customer_metrics",  // ❌ Unnecessary - matches filename
  schema: "looker"
}

-- CORRECT: Omit name when it matches filename
-- File: looker_customer_metrics.sqlx
config {
  type: "table",  // ✅ Name defaults to filename
  schema: "looker"
}

-- CORRECT: Specify name only when different from filename
-- File: looker_customer_metrics_v2.sqlx
config {
  type: "table",
  name: "looker_customer_metrics",  // ✅ Necessary - differs from filename
  schema: "looker"
}
```

### 3. Acuantia Dataset Conventions

**Primary Datasets**:
- `acuantia.ods` - Master operational data store (source of truth)
- `acuantia.ods_dev` / `acuantia.ods_prod` - ODS staging datasets
- `acuantia.looker_prod` - Production Looker tables
- `acuantia.looker_dev` - Development Looker tables
- `acuantia.reports_prod` - Production reports and views used outside Looker (typically linked to Google Sheets)
- `acuantia.reports_dev` - Development reports and views used outside Looker
- `acuantia.dataform` - Operations and temp tables
- `acuantia.callrail_api` - CallRail raw data
- `acuantia.dialpad_api` - Dialpad raw data
- `acuantia.hubspot` - HubSpot data (via Fivetran)
- `acuantia.magento_rotoplas_me_22_prod` - Magento/Adobe Commerce data (via Fivetran)

**Note on reports datasets**: When creating tables/views in `reports_*` datasets, use case-insensitive collation for string columns to ensure compatibility with Google Sheets connections. Apply collation at table/column creation time using `COLLATE 'und:ci'`.

**Schema suffix behavior**:
```bash
# With --schema-suffix dev
looker_prod → looker_dev
reports_prod → reports_dev
ods → ods (no suffix, use two-arg ref)
dataform → dataform_dev
```

### 4. Looker Integration Context

Tables in `definitions/output/looker/` feed Acuantia's Looker instance at https://looker.acuantia.com.

**Optimization requirements**:
- Add partitioning/clustering for query performance (Looker users run ad-hoc queries)
- Use descriptive column names (Looker dimension names derive from these)
- Include comprehensive column descriptions (synced to Looker metadata via scripts)
- Consider common Looker user query patterns (filters, aggregations)

**Looker-specific config pattern**:
```sql
config {
  type: "table",
  schema: "looker",  // Base name - DO NOT use "looker_prod"
  tags: ["looker", "daily"],
  bigquery: {
    partitionBy: "DATE(order_date)",
    clusterBy: ["customer_id", "region"]
  },
  columns: {
    customer_id: "Unique customer identifier from SAP (KUNNR field)",
    order_date: "Date when order was placed",
    region: "Geographic region for reporting (matches Looker region dimension)"
  }
}
```

**Metadata sync**: Use `node scripts/updateLookerDescriptions.js` in `acuantia-gcp-dataform` to sync column descriptions to Looker views.

### 5. Reports Dataset Integration

Tables in `definitions/output/reports/` are designed for use outside the Looker subsystem, typically connected to Google Sheets for ad-hoc reporting and data sharing.

**Use cases**:
- Google Sheets data connections for business users
- Ad-hoc reports shared with stakeholders
- Export tables for external systems
- Simplified views for non-technical users

**CRITICAL: Reports dataset schema configuration**:

**NEVER use `schema: "reports_prod"` or `schema: "reports_dev"` in SQLX files.**

The `--schema-suffix` flag automatically appends `_prod` or `_dev` to the schema name. Using `schema: "reports_prod"` would incorrectly create `reports_prod_prod`.

**CORRECT pattern**:
```sql
config {
  type: "table",  // or "view" depending on use case
  schema: "reports",  // Will resolve to reports_dev or reports_prod
  tags: ["reports", "google_sheets"],
  description: "Customer summary for Google Sheets integration",
  columns: {
    customer_name: {
      description: "Customer full name",
      bigqueryPolicyTags: ["COLLATE 'und:ci'"]  // Case-insensitive for Google Sheets
    },
    email: {
      description: "Customer email address",
      bigqueryPolicyTags: ["COLLATE 'und:ci'"]
    }
  }
}
```

**Schema resolution**:
- `schema: "reports"` + `--schema-suffix dev` → `acuantia.reports_dev`
- `schema: "reports"` + `--schema-suffix prod` → `acuantia.reports_prod`

**Case-insensitive collation requirement**:
When creating tables in `reports_*` datasets, apply case-insensitive collation to string columns:

```sql
CREATE TABLE `acuantia.reports_prod.customer_export` (
  customer_name STRING COLLATE 'und:ci',
  email STRING COLLATE 'und:ci',
  order_count INT64
);
```

**Why case-insensitivity matters**:
- Google Sheets connections often require case-insensitive string matching
- Prevents duplicate entries from case variations (e.g., "John" vs "JOHN")
- Simplifies filtering and lookups for business users

**IMPORTANT**: Always use base schema name without suffix:
- Use `schema: "reports"` in SQLX files (NOT `"reports_dev"` or `"reports_prod"`)
- The `--schema-suffix` flag handles the environment:
  - `--schema-suffix dev` → `reports_dev`
  - `--schema-suffix prod` → `reports_prod`

### 6. Source System Integration

Acuantia integrates data from multiple source systems. Use specific terminology when documenting columns:

**SAP ERP**:
```sql
columns: {
  customer_id: "SAP Customer Number (KUNNR) - unique identifier in SAP ERP",
  customer_name: "Customer name (NAME1 field) - legal business name",
  account_group: "Customer Account Group (KTOKD) - classification code"
}
```

**Dialpad API** (from `dialpad_data_integration` project):
```sql
-- Source declaration
-- definitions/sources/dialpad/calls.sqlx
config {
  type: "declaration",
  database: "acuantia",
  schema: "dialpad_api",
  name: "calls",
  description: "Dialpad call records with transcripts and sentiment analysis",
  columns: {
    call_id: "Unique call identifier from Dialpad API",
    transcript: "Full call transcript from Dialpad AI",
    sentiment: "Overall call sentiment: positive/negative/neutral/mixed"
  }
}
```

**CallRail API** (from `callrail_data_export` project):
```sql
-- Source declaration
-- definitions/sources/callrail/calls.sqlx
config {
  type: "declaration",
  database: "acuantia",
  schema: "callrail_api",
  name: "calls",
  columns: {
    call_id: "Unique CallRail call identifier",
    tracking_phone_number: "CallRail tracking number that received the call",
    attribution: "Nested attribution data (source, medium, campaign)"
  }
}
```

**HubSpot CRM** (via Fivetran):
```sql
config {
  type: "declaration",
  database: "acuantia",
  schema: "hubspot",
  name: "contact"
}
```

**Magento/Adobe Commerce** (via Fivetran):
```sql
config {
  type: "declaration",
  database: "acuantia",
  schema: "magento_rotoplas_me_22_prod",
  name: "sales_order"
}
```

### 7. Cross-Project Coordination

Acuantia's data platform spans multiple projects that work together:

```
callrail_data_export/          → acuantia.callrail_api.*
dialpad_data_integration/      → acuantia.dialpad_api.*
acuantia-gcp-dataform/         → Transform and model
looker/                        → Visualize and report
```

**When modifying schemas**:
1. **Source changes** (callrail_data_export or dialpad_data_integration):
   - Update Python schema definitions
   - Test with small data exports
   - Deploy to production

2. **Dataform updates** (acuantia-gcp-dataform):
   - Update source declarations in `definitions/sources/`
   - Modify transformations if needed
   - Update `definitions/output/looker/` tables
   - Test with `--schema-suffix dev`

3. **Looker updates** (looker project):
   - Update view definitions
   - Add new dimensions/measures
   - Test in development environment

**Schema change protocol**: Always coordinate changes across all three layers (raw → transformed → visualization).

### 8. Business Context

Acuantia serves four main product verticals:
- **Septic**: Septic tank systems
- **General**: General purpose containers
- **Industrial**: Industrial containers and equipment
- **Chemical**: Chemical storage containers

**Key business entities**:
- TankHolding: Key business vertical with specialized recovery operations
- Customer Journey: Multi-touch attribution across CallRail, HubSpot, and Magento
- Voice of Customer (VoC): Dialpad call transcripts analyzed for sentiment and topics

**When creating tables**, consider how they support these business verticals and use cases.

## Validation Queries (Acuantia-Specific)

```bash
# Check Looker dev tables
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`acuantia.looker_dev.looker_customer_metrics\`"

# Check reports dev tables
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`acuantia.reports_dev.customer_export\`"

# Check ODS tables
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`acuantia.ods.sap_customers\`"

# Verify CallRail data freshness
bq query --use_legacy_sql=false \
  "SELECT MAX(start_time) FROM \`acuantia.callrail_api.calls\`"

# Verify Dialpad data freshness
bq query --use_legacy_sql=false \
  "SELECT MAX(start_time) FROM \`acuantia.dialpad_api.calls\`"
```

## Common Acuantia-Specific Mistakes

### Mistake 1: Using single-argument ref() for ODS tables

```sql
-- WRONG: Creates ods_dev_dev with --schema-suffix dev
FROM ${ref("sap_customers")}

-- CORRECT: Two-argument ref() for ODS
FROM ${ref("ods", "sap_customers")}
```

### Mistake 2: Skipping intermediate view layer for Looker tables

```
# WRONG: Table directly in output folder without intermediate view
definitions/output/looker/looker_customer_metrics.sqlx
config { type: "table", schema: "looker_prod" }
SELECT customer_id, SUM(order_total) FROM ...

# CORRECT: Two-layer pattern
definitions/intermediate/looker/vw_looker_customer_metrics.sqlx
config { type: "view", schema: "dataform" }
SELECT customer_id, SUM(order_total) FROM ...

definitions/output/looker/looker_customer_metrics.sqlx
config { type: "table", schema: "looker_prod" }
SELECT * FROM ${ref("vw_looker_customer_metrics")}
```

### Mistake 3: Missing looker_ prefix or wrong view prefix

```
# WRONG - Missing prefix
definitions/output/looker/customer_metrics.sqlx

# WRONG - View without vw_ prefix
definitions/intermediate/looker/looker_customer_metrics.sqlx

# CORRECT - Proper naming
definitions/intermediate/looker/vw_looker_customer_metrics.sqlx
definitions/output/looker/looker_customer_metrics.sqlx
```

### Mistake 4: Using "view" type in output/looker folder

```sql
-- WRONG: View in output folder (should be table)
-- definitions/output/looker/looker_sales.sqlx
config {
  type: "view",  // ❌ Wrong - must be "table"
  schema: "looker_prod"
}

-- CORRECT: Table in output folder
-- definitions/output/looker/looker_sales.sqlx
config {
  type: "table",  // ✅ Correct
  schema: "looker_prod"
}
```

### Mistake 5: Using wrong schema for Looker tables or including suffix

```sql
-- WRONG: Wrong schema name
config {
  type: "table",
  schema: "reporting"  // Not Looker-specific
}

-- WRONG: Including suffix in schema name
config {
  type: "table",
  schema: "looker_prod"  // Will create looker_prod_prod ❌
}

-- CORRECT: Base schema name
config {
  type: "table",
  schema: "looker"  // Suffix appended automatically ✅
}
```

### Mistake 6: Using suffixed schema names for reports datasets

```sql
-- WRONG: Including suffix in schema name
config {
  type: "table",
  schema: "reports_prod"  // Will create reports_prod_prod ❌
}

-- WRONG: Using dev suffix
config {
  type: "table",
  schema: "reports_dev"  // Will create reports_dev_dev ❌
}

-- CORRECT: Base schema name
config {
  type: "table",
  schema: "reports"  // Suffix appended automatically ✅
}
```

### Mistake 7: Hardcoding acuantia.ods in queries

```sql
-- WRONG: Hardcoded path
FROM `acuantia.ods.sap_customers`

-- CORRECT: Use two-argument ref()
FROM ${ref("ods", "sap_customers")}
```

## Red Flags - Acuantia-Specific

If you're thinking any of these thoughts, STOP:

- "I'll use single-argument ref() for ODS tables (it's simpler)"
- "I don't need an intermediate view, I'll put the logic directly in the output table"
- "I'll create a view in definitions/output/looker/ instead of a table"
- "I don't need the looker_ prefix for this Looker table"
- "I don't need the vw_ prefix for this intermediate view"
- "I'll use `schema: 'looker_prod'` instead of `schema: 'looker'`"
- "I'll use `schema: 'reports_prod'` instead of `schema: 'reports'`"
- "The schema suffix is just for dev, I should hardcode _prod for production"
- "I'll add `name:` to the config even though it matches the filename"
- "I'll skip coordinating with the looker/ project team"
- "I don't need to check CallRail/Dialpad data freshness"

**All of these mean**: You're about to break Acuantia conventions. Follow the patterns above.

## Quick Reference

| Pattern | Acuantia Convention |
|---------|---------------------|
| ODS tables | Two-argument ref(): `${ref("ods", "table_name")}` |
| Looker intermediate views | `definitions/intermediate/looker/vw_looker_*.sqlx` (type: "view") |
| Looker output tables | `definitions/output/looker/looker_*.sqlx` (type: "table", sources from `vw_looker_*`) |
| Looker schema | Intermediate: `schema: "dataform"`, Output: `schema: "looker"` (NOT "looker_prod") |
| Reports tables | `definitions/output/reports/*.sqlx` (use `schema: "reports"` NOT "reports_prod") |
| Reports collation | Use `COLLATE 'und:ci'` for string columns (case-insensitive for Google Sheets) |
| Schema suffixes | NEVER hardcode `_prod` or `_dev` - use `--schema-suffix` flag instead |
| Config name | Omit `name:` if it matches filename - only specify when different |
| CallRail data | `acuantia.callrail_api.*` |
| Dialpad data | `acuantia.dialpad_api.*` |
| HubSpot data | `acuantia.hubspot.*` |
| Magento data | `acuantia.magento_rotoplas_me_22_prod.*` |
| Dev testing | `--schema-suffix dev` (see dataform-engineering-fundamentals) |
| Looker metadata | Run `node scripts/updateLookerDescriptions.js` |

## Summary

This skill adds **only Acuantia-specific patterns**. For all generic Dataform practices:
- TDD workflow
- Safety practices
- ${ref()} enforcement (general cases)
- Documentation standards
- Architecture patterns
- Troubleshooting

**→ See `dataform-engineering-fundamentals` skill.**

The patterns in this skill (ODS two-arg ref, looker_ prefix, Acuantia datasets, cross-project coordination) are **required additions** to the generic foundation, not replacements.
