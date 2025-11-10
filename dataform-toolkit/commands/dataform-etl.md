---
description: Launch ETL agent for BigQuery Dataform development
---

You are launching the ETL Dataform engineer agent to handle data transformation pipeline work.

**Purpose**: The ETL agent specializes in BigQuery Dataform projects, SQLX files, data quality, and pipeline development. Use this for:
- Complex Dataform transformations
- Pipeline troubleshooting
- Data quality implementations
- ELT workflow coordination

**Task**: Use the Task tool with `subagent_type="etl"` to launch the ETL agent. Pass the user's request as the prompt, including:
- What they need to accomplish
- Any relevant context about tables, datasets, or business logic
- Whether this is new development, modification, or troubleshooting

The ETL agent has access to the dataform-engineering-fundamentals skill and will follow best practices for BigQuery Dataform development.

**Example**:
```
User asks: "Help me create a customer metrics table"
You launch: Task tool with subagent_type="etl" and prompt="Create a customer metrics table in Dataform following TDD workflow. Ask user about required metrics and data sources."
```
