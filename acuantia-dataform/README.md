# acuantia-dataform

Acuantia-specific patterns for BigQuery Dataform development.

## Overview

This plugin extends the `dataform-engineering-fundamentals` skill with Acuantia-specific conventions for working with the `acuantia-gcp-dataform` project. It provides guidance on ODS architecture, Looker integration, and cross-project coordination with CallRail and Dialpad data pipelines.

## What This Plugin Provides

### Skills

- **acuantia-dataform** - Acuantia-specific Dataform patterns including:
  - ODS two-argument ref() syntax (`${ref("ods", "table_name")}`)
  - Looker table naming conventions (looker_ prefix, two-layer view/table pattern)
  - Integration with acuantia datasets (looker_prod, reports_prod, callrail_api, dialpad_api)
  - Cross-project coordination protocols
  - Business context for Acuantia's product verticals

## Installation

This plugin is part of the ihistand marketplace:

```bash
/plugin marketplace add ihistand
/plugin install acuantia-dataform@ihistand
```

## Usage

The skill automatically triggers when working on:
- The `acuantia-gcp-dataform` project
- Tables that integrate with Acuantia's Looker instance
- Transformations using Acuantia's ODS architecture
- Pipelines coordinating with callrail_data_export or dialpad_data_integration projects

### Key Patterns

**ODS Two-Argument ref():**
```sql
-- CORRECT: Two-argument ref() for ODS tables
FROM ${ref("ods", "sap_customers")}

-- WRONG: Single-argument causes ods_dev_dev with --schema-suffix dev
FROM ${ref("sap_customers")}
```

**Looker Two-Layer Architecture:**
```
definitions/intermediate/looker/vw_looker_customer_metrics.sqlx  (view with logic)
definitions/output/looker/looker_customer_metrics.sqlx           (table from view)
```

**Schema Naming:**
```sql
config {
  type: "table",
  schema: "looker"  // NOT "looker_prod" - suffix added automatically
}
```

## Prerequisites

This skill requires the `dataform-engineering-fundamentals` skill. Install the `dataform-toolkit` plugin first:

```bash
/plugin install dataform-toolkit@ihistand
```

## Documentation

See the skill file for comprehensive documentation on:
- ODS architecture and ref() syntax
- Looker table naming conventions
- Reports dataset integration
- Source system integration (SAP, Dialpad, CallRail, HubSpot, Magento)
- Cross-project coordination protocols
- Business context and verticals

## Author

**Ivan Histand** - Sr Data Architect
Email: ihistand@rotoplas.com
GitHub: [@ihistand](https://github.com/ihistand)

## Version

1.0.0 - Initial release
