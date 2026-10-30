---
prd: {{project}}
version: 0.1.0
status: Draft
owner: {{owner}}
updated: {{date}}
sql-dialect: {{sql_dialect}}
---

<!-- Format: references/prd-format.md, "prd.md sections". -->
<!-- The first approval goes through the prd-toolkit:authoring-prds skill (phase 7 gates); every later change and approval goes through prd-toolkit:changing-prds (step 5). -->

# {{project}}

## 1. Metadata & stack

- Language: [NEEDS CLARIFICATION: language and version]
- Framework: [NEEDS CLARIFICATION: framework and version]
- Database: [NEEDS CLARIFICATION: database and version]
- Hosting: [NEEDS CLARIFICATION: where it runs]
- Repository: [NEEDS CLARIFICATION: repository URL]
- Not used: [NEEDS CLARIFICATION: technologies ruled out]

## 2. Summary & goals

[NEEDS CLARIFICATION: what does this product do, and for whom, in two sentences]

Goals:

- [NEEDS CLARIFICATION: first measurable goal]

Personas: [NEEDS CLARIFICATION: who uses it]

Out of scope: [NEEDS CLARIFICATION: what this PRD deliberately excludes]

## 3. Glossary

| Term | Meaning | Banned synonyms |
|---|---|---|
| [NEEDS CLARIFICATION: first domain term] | [NEEDS CLARIFICATION: its meaning] | none |

## 4. Architecture

[NEEDS CLARIFICATION: components and how they connect; add a mermaid diagram]

## 5. Standards registry

| Object (glob) | Linter command | Rules live in | Applies to | Decision |
|---|---|---|---|---|
| [NEEDS CLARIFICATION: file glob] | [NEEDS CLARIFICATION: linter command] | [NEEDS CLARIFICATION: where the rules live] | [NEEDS CLARIFICATION: who or what it applies to] | proposed |

## 6. Skills registry

| Object or activity | Skill | Decision |
|---|---|---|
| [NEEDS CLARIFICATION: activity] | [NEEDS CLARIFICATION: skill name] | proposed |

## 7. Contract types

| Type | Files (glob) | Validator |
|---|---|---|
| openapi | `contracts/openapi.yaml` | built-in |
| schema | `contracts/schema.sql` | built-in |
| events | `contracts/events.md` | built-in |
| errors | `contracts/errors.yaml` | built-in |
| permissions | `contracts/permissions.yaml` | built-in |
| config | `contracts/config.yaml` | built-in |
| classification | `contracts/data-classification.yaml` | built-in |
| dependencies | `contracts/dependencies/*.yaml` | built-in |
| fixtures | `contracts/fixtures/**` | built-in |

[NEEDS CLARIFICATION: for each contract listed above, populate its file, or delete the file, drop its row here and add a section 1 line in the form: - Not applicable: (the file path in backticks) — (the reason). contracts/errors.yaml is mandatory: always populate it, never delete it]

## 8. Adoption map

[NEEDS CLARIFICATION: new project, or an existing system to adopt? Replace this line with `Not applicable: new project`, or the `| Area | State | Boundary |` table]

## 9. Versioning

- Breaking for the API: [NEEDS CLARIFICATION: what counts as breaking]
- Breaking for the schema: [NEEDS CLARIFICATION: what counts as breaking]
- Breaking for events: [NEEDS CLARIFICATION: what counts as breaking]
- Compatibility window: [NEEDS CLARIFICATION: how long old behaviour is kept]
- Migration rule: [NEEDS CLARIFICATION: how changes roll out]

## 10. Design & UI

[NEEDS CLARIFICATION: does the product have a user interface? Describe it, or replace this line with `Not applicable: <reason>`]

## 11. Requirement index

| ID | Title | Status | File | Since |
|---|---|---|---|---|

## 12. Assumptions index

| ID | Assumption | Status |
|---|---|---|

## 13. Open questions

- Q-01 [NEEDS CLARIFICATION: what is the first question to settle with the owner]

## 14. Changelog

| Version | Date | Change | IDs |
|---|---|---|---|
| 0.1.0 | {{date}} | Draft started | none |
