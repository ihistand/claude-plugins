# Claude Plugins Docs Web App — Design Spec

**Date:** 2026-03-21
**Status:** Approved

## Purpose

A developer documentation hub for the `claude-plugins` marketplace. Primary audience: developers installing and using the plugins. Purpose: technical reference, not marketing.

## Tech Stack

- **Vite + vanilla JS** — no framework, minimal dependencies, fast dev loop
- **Hash-based client-side routing** — no server required; works with `vite dev` or opening `dist/index.html` directly
- **Static content** — plugin data hardcoded in `src/data/plugins.js`; no markdown parsing at runtime

## Project Structure

```
claude-plugins/web/
├── index.html
├── vite.config.js
├── package.json
├── src/
│   ├── main.js           # app bootstrap + hash router
│   ├── style.css         # global styles + sidebar layout
│   ├── data/
│   │   └── plugins.js    # plugin metadata, commands, skills (static JS object)
│   └── pages/
│       ├── home.js       # overview page — all plugins as summary cards
│       └── plugin.js     # per-plugin detail view
```

## Layout

**Sidebar nav + main content pane.** The sidebar is fixed-width on the left; the main pane fills remaining space.

- Sidebar: site title, "Overview" link, then a "PLUGINS" section listing each plugin by name
- Active item is highlighted; clicking updates the URL hash and swaps main pane content
- No mobile breakpoint required for now

## Visual Style

**Clean Light** — white/gray background, indigo accents (`#4f46e5`), system font (`system-ui, sans-serif`), monospace for code/commands.

Reference: Stripe Docs / Linear aesthetic — polished, readable, minimal.

Color tokens:
- Background: `#f8f9fa`
- Sidebar bg: `#fff`, border: `#e5e7eb`
- Active/accent: `#4f46e5`
- Body text: `#111`
- Secondary text: `#6b7280`
- Muted labels: `#9ca3af`
- Code blocks: `#f3f4f6` bg, `1px solid #e5e7eb` border

## Routing

Hash-based. Routes:

| Hash | Page |
|------|------|
| `#` or empty | Overview (home) |
| `#dataform-toolkit` | dataform-toolkit detail |
| `#stl-generator-toolkit` | stl-generator-toolkit detail |
| `#acuantia-dataform` | acuantia-dataform detail |

`main.js` listens to `hashchange` and `DOMContentLoaded` events, reads `location.hash`, and renders the appropriate page into `#main-content`.

## Content Data (`plugins.js`)

A single exported array of plugin objects. **Descriptions are paraphrased for brevity** — they do not need to match plugin.json verbatim.

The **Commands table section is omitted entirely** from the detail page if `commands` is an empty array (e.g., acuantia-dataform has no commands).

```js
export const plugins = [
  {
    id: "dataform-toolkit",
    name: "dataform-toolkit",
    version: "1.0.0",
    description: "Comprehensive toolkit for BigQuery Dataform development with TDD workflow and ETL agent integration",
    install: "/plugin install dataform-toolkit@ihistand",
    commands: [
      { name: "/dataform-test", description: "Test tables in dev environment", workflow: "compile → dry-run → dev execution → validation" },
      { name: "/dataform-deploy", description: "Deploy to production safely", workflow: "Verify dev testing → Check tests pass → Production deploy" },
      { name: "/dataform-new-table", description: "Create new table with TDD", workflow: "RED (tests fail) → GREEN (tests pass) → REFACTOR" },
      { name: "/dataform-etl", description: "Launch ETL agent", workflow: "Complex transformations, troubleshooting, data quality" },
    ],
    skills: [
      { name: "dataform-engineering-fundamentals", description: "Enforces TDD workflow, ref() usage, safety practices, and documentation standards" }
    ],
    references: [
      { label: "Dataform Documentation", url: "https://cloud.google.com/dataform/docs" },
      { label: "BigQuery GoogleSQL Reference", url: "https://cloud.google.com/bigquery/docs/reference/standard-sql" },
    ]
  },
  {
    id: "stl-generator-toolkit",
    name: "stl-generator-toolkit",
    version: "1.0.0",
    description: "Generate 3D printable STL files for woodworking jigs and fixtures using CadQuery, with pre-built scripts and parametric design patterns",
    install: "/plugin install stl-generator-toolkit@ihistand",
    commands: [
      { name: "/stl-generate", description: "Generate custom STL for any woodworking jig", workflow: "Gather requirements → Check pre-built scripts → Generate → Export STL" },
      { name: "/stl-circle-jig", description: "Generate circle cutting jig for router work", workflow: "Get outer/inner diameter → Run script → Export STL" },
      { name: "/stl-angle-wedge", description: "Generate angle guide wedge for compound cuts", workflow: "Get angle (1–60°) → Run script → Export STL" },
      { name: "/stl-spacing-block", description: "Create precision spacing blocks for assembly", workflow: "Get height/dimensions → Run script → Export STL" },
    ],
    skills: [
      { name: "stl-generator", description: "Pre-built CadQuery scripts, printer specs (Elegoo Neptune 4 Pro), and parametric design patterns for woodworking jigs" }
    ],
    references: []
  },
  {
    id: "acuantia-dataform",
    name: "acuantia-dataform",
    version: "1.0.0",
    description: "Acuantia-specific patterns for BigQuery Dataform — ODS two-arg ref() syntax, looker_ filename conventions, and cross-project coordination",
    install: "/plugin install acuantia-dataform@ihistand",
    commands: [],   // no slash commands — skills only
    skills: [
      { name: "acuantia-dataform", description: "Extends dataform-engineering-fundamentals with Acuantia-specific conventions: ODS two-arg ref(), looker_ prefixes, acuantia dataset schemas, and Looker integration patterns" }
    ],
    references: []
  },
]
```

## Per-Plugin Detail Page

Rendered by `plugin.js`, sections in order:

1. **Header** — plugin name (h1), version badge, one-line description
2. **Installation block** — gray code box with copyable install command
3. **Commands table** — columns: Command, Description, Key Workflow. **Omit this section entirely if `commands` is empty.**
4. **Skills section** — skill name + what discipline it enforces
5. **References** (if any) — linked list of external docs. Omit if `references` is empty.

## Overview / Home Page

Rendered by `home.js`. Three plugin summary cards in a vertical list (not a grid — easier to read). Each card shows: name, description, install snippet, link to full detail page.

## Dev Setup

```bash
cd claude-plugins/web
npm install
npm run dev    # http://localhost:5173
npm run build  # outputs to dist/
```

`vite.config.js` must set `base: './'` so that `dist/index.html` works when opened directly from the filesystem (not via a dev server):

```js
// vite.config.js
export default {
  base: './',
}
```

No deployment target defined yet.

## Out of Scope

- Search
- Dark/light mode toggle
- Mobile responsive layout
- Versioning / changelog
- Markdown rendering at runtime
