# Claude Plugins Docs Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vite + vanilla JS developer documentation hub for the claude-plugins marketplace with a sidebar nav + content pane layout.

**Architecture:** Hash-based SPA — `main.js` listens to `hashchange`/`DOMContentLoaded`, reads `location.hash`, and renders the appropriate page (home or plugin detail) into `#main-content`. All plugin data is hardcoded in `plugins.js`; pages are pure functions that take a plugin object and return an HTML string.

**Tech Stack:** Vite 5, vanilla JS (ESM), Vitest (unit tests), no frameworks.

**Spec:** `docs/superpowers/specs/2026-03-21-claude-plugins-web-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `web/index.html` | HTML shell — sidebar skeleton + `#main-content` mount point |
| `web/vite.config.js` | Vite config with `base: './'` for filesystem-direct builds |
| `web/package.json` | Scripts: dev, build, test |
| `web/src/style.css` | Layout (sidebar + main), visual tokens, all component styles |
| `web/src/data/plugins.js` | Static plugin data array (all 3 plugins) |
| `web/src/pages/home.js` | Returns HTML string for overview page (plugin card list) |
| `web/src/pages/plugin.js` | Returns HTML string for plugin detail page |
| `web/src/main.js` | App bootstrap + hash router + sidebar active state |
| `web/src/data/plugins.test.js` | Data integrity tests |
| `web/src/pages/home.test.js` | Home page rendering tests |
| `web/src/pages/plugin.test.js` | Plugin detail page rendering tests |
| `web/src/main.test.js` | Router logic tests |

---

## Task 1: Project Scaffold

**Files:**
- Create: `web/package.json`
- Create: `web/vite.config.js`
- Create: `web/index.html`

- [ ] **Step 1: Create `web/package.json`**

```json
{
  "name": "claude-plugins-docs",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "vitest": "^1.6.0"
  }
}
```

- [ ] **Step 2: Create `web/vite.config.js`**

```js
export default {
  base: './',
}
```

- [ ] **Step 3: Create `web/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Plugins Docs</title>
  <link rel="stylesheet" href="/src/style.css">
</head>
<body>
  <div id="app">
    <nav id="sidebar">
      <div class="sidebar-brand">Claude Plugins</div>
      <ul class="nav-list">
        <li><a href="#" class="nav-link" data-hash="">Overview</a></li>
        <li class="nav-section-label">PLUGINS</li>
        <li><a href="#dataform-toolkit" class="nav-link" data-hash="dataform-toolkit">dataform-toolkit</a></li>
        <li><a href="#stl-generator-toolkit" class="nav-link" data-hash="stl-generator-toolkit">stl-generator-toolkit</a></li>
        <li><a href="#acuantia-dataform" class="nav-link" data-hash="acuantia-dataform">acuantia-dataform</a></li>
      </ul>
    </nav>
    <main id="main-content"></main>
  </div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Install dependencies**

```bash
cd web
npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 5: Verify dev server starts**

```bash
npm run dev
```

Expected: Vite starts at `http://localhost:5173`. Browser shows blank page (no JS yet). Stop server with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
cd web
git add package.json vite.config.js index.html package-lock.json
git commit -m "feat(web): scaffold Vite project with index.html"
```

---

## Task 2: Plugin Data

**Files:**
- Create: `web/src/data/plugins.js`
- Create: `web/src/data/plugins.test.js`

- [ ] **Step 1: Write the failing test**

Create `web/src/data/plugins.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { plugins } from './plugins.js'

describe('plugins data', () => {
  it('exports an array of 3 plugins', () => {
    expect(Array.isArray(plugins)).toBe(true)
    expect(plugins).toHaveLength(3)
  })

  it('each plugin has required fields', () => {
    for (const p of plugins) {
      expect(typeof p.id).toBe('string')
      expect(typeof p.name).toBe('string')
      expect(typeof p.version).toBe('string')
      expect(typeof p.description).toBe('string')
      expect(typeof p.install).toBe('string')
      expect(Array.isArray(p.commands)).toBe(true)
      expect(Array.isArray(p.skills)).toBe(true)
      expect(Array.isArray(p.references)).toBe(true)
    }
  })

  it('install commands use @ihistand suffix', () => {
    for (const p of plugins) {
      expect(p.install).toContain('@ihistand')
    }
  })

  it('each command has name, description, and workflow', () => {
    for (const p of plugins) {
      for (const cmd of p.commands) {
        expect(typeof cmd.name).toBe('string')
        expect(typeof cmd.description).toBe('string')
        expect(typeof cmd.workflow).toBe('string')
      }
    }
  })

  it('acuantia-dataform has no commands', () => {
    const acuantia = plugins.find(p => p.id === 'acuantia-dataform')
    expect(acuantia.commands).toHaveLength(0)
  })

  it('plugin ids match known routes', () => {
    const ids = plugins.map(p => p.id)
    expect(ids).toContain('dataform-toolkit')
    expect(ids).toContain('stl-generator-toolkit')
    expect(ids).toContain('acuantia-dataform')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd web
npm test
```

Expected: FAIL — `plugins.js` does not exist.

- [ ] **Step 3: Create `web/src/data/plugins.js`**

```js
export const plugins = [
  {
    id: 'dataform-toolkit',
    name: 'dataform-toolkit',
    version: '1.0.0',
    description: 'Comprehensive toolkit for BigQuery Dataform development with TDD workflow and ETL agent integration',
    install: '/plugin install dataform-toolkit@ihistand',
    commands: [
      { name: '/dataform-test', description: 'Test tables in dev environment', workflow: 'compile → dry-run → dev execution → validation' },
      { name: '/dataform-deploy', description: 'Deploy to production safely', workflow: 'Verify dev testing → Check tests pass → Production deploy' },
      { name: '/dataform-new-table', description: 'Create new table with TDD', workflow: 'RED (tests fail) → GREEN (tests pass) → REFACTOR' },
      { name: '/dataform-etl', description: 'Launch ETL agent', workflow: 'Complex transformations, troubleshooting, data quality' },
    ],
    skills: [
      { name: 'dataform-engineering-fundamentals', description: 'Enforces TDD workflow, ref() usage, safety practices, and documentation standards' },
    ],
    references: [
      { label: 'Dataform Documentation', url: 'https://cloud.google.com/dataform/docs' },
      { label: 'BigQuery GoogleSQL Reference', url: 'https://cloud.google.com/bigquery/docs/reference/standard-sql' },
    ],
  },
  {
    id: 'stl-generator-toolkit',
    name: 'stl-generator-toolkit',
    version: '1.0.0',
    description: 'Generate 3D printable STL files for woodworking jigs and fixtures using CadQuery, with pre-built scripts and parametric design patterns',
    install: '/plugin install stl-generator-toolkit@ihistand',
    commands: [
      { name: '/stl-generate', description: 'Generate custom STL for any woodworking jig', workflow: 'Gather requirements → Check pre-built scripts → Generate → Export STL' },
      { name: '/stl-circle-jig', description: 'Generate circle cutting jig for router work', workflow: 'Get outer/inner diameter → Run script → Export STL' },
      { name: '/stl-angle-wedge', description: 'Generate angle guide wedge for compound cuts', workflow: 'Get angle (1–60°) → Run script → Export STL' },
      { name: '/stl-spacing-block', description: 'Create precision spacing blocks for assembly', workflow: 'Get height/dimensions → Run script → Export STL' },
    ],
    skills: [
      { name: 'stl-generator', description: 'Pre-built CadQuery scripts, printer specs (Elegoo Neptune 4 Pro), and parametric design patterns for woodworking jigs' },
    ],
    references: [],
  },
  {
    id: 'acuantia-dataform',
    name: 'acuantia-dataform',
    version: '1.0.0',
    description: 'Acuantia-specific patterns for BigQuery Dataform — ODS two-arg ref() syntax, looker_ filename conventions, and cross-project coordination',
    install: '/plugin install acuantia-dataform@ihistand',
    commands: [],
    skills: [
      { name: 'acuantia-dataform', description: 'Extends dataform-engineering-fundamentals with Acuantia-specific conventions: ODS two-arg ref(), looker_ prefixes, acuantia dataset schemas, and Looker integration patterns' },
    ],
    references: [],
  },
]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/data/plugins.js web/src/data/plugins.test.js
git commit -m "feat(web): add plugin data with tests"
```

---

## Task 3: CSS Styles

**Files:**
- Create: `web/src/style.css`

No unit tests for CSS — visual verification in Task 7.

- [ ] **Step 1: Create `web/src/style.css`**

```css
/* Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* Layout */
body {
  font-family: system-ui, -apple-system, sans-serif;
  background: #f8f9fa;
  color: #111;
  height: 100vh;
  overflow: hidden;
}

#app {
  display: flex;
  height: 100vh;
}

/* Sidebar */
#sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px 0;
}

.sidebar-brand {
  font-size: 13px;
  font-weight: 700;
  color: #111;
  padding: 0 16px 20px;
  letter-spacing: -0.01em;
}

.nav-list {
  list-style: none;
  padding: 0;
}

.nav-section-label {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  letter-spacing: 0.06em;
  padding: 12px 16px 4px;
}

.nav-link {
  display: block;
  font-size: 13px;
  color: #374151;
  text-decoration: none;
  padding: 5px 16px;
  border-radius: 4px;
  margin: 1px 8px;
  transition: background 0.1s, color 0.1s;
}

.nav-link:hover {
  background: #f3f4f6;
  color: #111;
}

.nav-link.active {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

/* Main content */
#main-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 48px;
  max-width: 860px;
}

/* Typography */
h1 { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 6px; }
h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; margin-top: 32px; }
p  { font-size: 14px; line-height: 1.6; color: #374151; }

/* Badge */
.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 2px 7px;
  margin-left: 8px;
  vertical-align: middle;
}

/* Description */
.plugin-description {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 24px;
  margin-top: 4px;
}

/* Install block */
.install-block {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.install-label {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  letter-spacing: 0.06em;
  flex-shrink: 0;
}

.install-cmd {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 13px;
  color: #4f46e5;
  flex: 1;
}

/* Section header */
.section-header {
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
  margin-top: 28px;
}

/* Commands table */
.commands-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 8px;
}

.commands-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  padding: 6px 12px 6px 0;
  border-bottom: 1px solid #e5e7eb;
}

.commands-table td {
  padding: 10px 12px 10px 0;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: top;
  color: #374151;
}

.commands-table td:first-child {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  color: #4f46e5;
  white-space: nowrap;
}

.commands-table td:last-child {
  color: #6b7280;
  font-size: 12px;
}

/* Skills list */
.skill-item {
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}

.skill-name {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 13px;
  color: #4f46e5;
  margin-bottom: 4px;
}

.skill-desc {
  font-size: 13px;
  color: #6b7280;
}

/* References */
.ref-list {
  list-style: none;
}

.ref-list li { margin-bottom: 6px; }

.ref-list a {
  font-size: 13px;
  color: #4f46e5;
  text-decoration: none;
}

.ref-list a:hover { text-decoration: underline; }

/* Home page cards */
.plugin-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 16px;
}

.plugin-card-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.plugin-card-name {
  font-size: 15px;
  font-weight: 600;
  color: #111;
}

.plugin-card-desc {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 14px;
  line-height: 1.5;
}

.plugin-card-install {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 12px;
  color: #4f46e5;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 6px 10px;
  display: inline-block;
  margin-bottom: 12px;
}

.plugin-card-link {
  font-size: 13px;
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
}

.plugin-card-link:hover { text-decoration: underline; }

/* Page title area */
.page-header { margin-bottom: 8px; }
.page-title-row { display: flex; align-items: center; gap: 0; }
```

- [ ] **Step 2: Commit**

```bash
git add web/src/style.css
git commit -m "feat(web): add CSS layout and component styles"
```

---

## Task 4: Home Page

**Files:**
- Create: `web/src/pages/home.js`
- Create: `web/src/pages/home.test.js`

- [ ] **Step 1: Write the failing test**

Create `web/src/pages/home.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { renderHome } from './home.js'
import { plugins } from '../data/plugins.js'

describe('renderHome', () => {
  let html

  beforeEach(() => {
    html = renderHome(plugins)
  })

  it('returns a string', () => {
    expect(typeof html).toBe('string')
  })

  it('renders a card for each plugin', () => {
    for (const p of plugins) {
      expect(html).toContain(p.name)
      expect(html).toContain(p.description)
      expect(html).toContain(p.install)
    }
  })

  it('renders links to each plugin detail page', () => {
    expect(html).toContain('#dataform-toolkit')
    expect(html).toContain('#stl-generator-toolkit')
    expect(html).toContain('#acuantia-dataform')
  })

  it('renders version badge for each plugin', () => {
    // all plugins are 1.0.0
    expect(html.match(/1\.0\.0/g).length).toBeGreaterThanOrEqual(3)
  })
})
```

- [ ] **Step 2: Add missing import to test**

The test uses `beforeEach` — add `beforeEach` to the import:

```js
import { describe, it, expect, beforeEach } from 'vitest'
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd web
npm test -- src/pages/home.test.js
```

Expected: FAIL — `home.js` does not exist.

- [ ] **Step 4: Create `web/src/pages/home.js`**

```js
/**
 * Renders the overview page — a list of plugin summary cards.
 * @param {Array} plugins - the plugins array from data/plugins.js
 * @returns {string} HTML string
 */
export function renderHome(plugins) {
  const cards = plugins.map(p => `
    <div class="plugin-card">
      <div class="plugin-card-header">
        <span class="plugin-card-name">${p.name}</span>
        <span class="badge">${p.version}</span>
      </div>
      <p class="plugin-card-desc">${p.description}</p>
      <div class="plugin-card-install">${p.install}</div>
      <br>
      <a href="#${p.id}" class="plugin-card-link">View docs &rarr;</a>
    </div>
  `).join('')

  return `
    <div class="page-header">
      <h1>Claude Plugins</h1>
      <p class="plugin-description">Developer documentation for the ihistand plugin marketplace.</p>
    </div>
    ${cards}
  `
}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
npm test -- src/pages/home.test.js
```

Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add web/src/pages/home.js web/src/pages/home.test.js
git commit -m "feat(web): add home page renderer with tests"
```

---

## Task 5: Plugin Detail Page

**Files:**
- Create: `web/src/pages/plugin.js`
- Create: `web/src/pages/plugin.test.js`

- [ ] **Step 1: Write the failing test**

Create `web/src/pages/plugin.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { renderPlugin } from './plugin.js'
import { plugins } from '../data/plugins.js'

const dataform = plugins.find(p => p.id === 'dataform-toolkit')
const acuantia = plugins.find(p => p.id === 'acuantia-dataform')
const stl = plugins.find(p => p.id === 'stl-generator-toolkit')

describe('renderPlugin', () => {
  it('returns a string', () => {
    expect(typeof renderPlugin(dataform)).toBe('string')
  })

  it('renders plugin name and version', () => {
    const html = renderPlugin(dataform)
    expect(html).toContain('dataform-toolkit')
    expect(html).toContain('1.0.0')
  })

  it('renders install command', () => {
    const html = renderPlugin(dataform)
    expect(html).toContain('/plugin install dataform-toolkit@ihistand')
  })

  it('renders commands table when commands exist', () => {
    const html = renderPlugin(dataform)
    expect(html).toContain('/dataform-test')
    expect(html).toContain('/dataform-deploy')
    expect(html).toContain('/dataform-new-table')
    expect(html).toContain('/dataform-etl')
  })

  it('omits commands section when commands array is empty', () => {
    const html = renderPlugin(acuantia)
    expect(html).not.toContain('commands-table')
    expect(html).not.toContain('COMMANDS')
  })

  it('renders skills section', () => {
    const html = renderPlugin(dataform)
    expect(html).toContain('dataform-engineering-fundamentals')
  })

  it('renders references when present', () => {
    const html = renderPlugin(dataform)
    expect(html).toContain('Dataform Documentation')
    expect(html).toContain('https://cloud.google.com/dataform/docs')
  })

  it('omits references section when references array is empty', () => {
    const html = renderPlugin(stl)
    expect(html).not.toContain('REFERENCES')
  })

  it('renders stl commands', () => {
    const html = renderPlugin(stl)
    expect(html).toContain('/stl-generate')
    expect(html).toContain('/stl-circle-jig')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- src/pages/plugin.test.js
```

Expected: FAIL — `plugin.js` does not exist.

- [ ] **Step 3: Create `web/src/pages/plugin.js`**

```js
/**
 * Renders a plugin detail page.
 * @param {Object} plugin - a single plugin object from data/plugins.js
 * @returns {string} HTML string
 */
export function renderPlugin(plugin) {
  const commandsSection = plugin.commands.length > 0 ? `
    <div class="section-header">COMMANDS</div>
    <table class="commands-table">
      <thead>
        <tr>
          <th>Command</th>
          <th>Description</th>
          <th>Key Workflow</th>
        </tr>
      </thead>
      <tbody>
        ${plugin.commands.map(cmd => `
          <tr>
            <td>${cmd.name}</td>
            <td>${cmd.description}</td>
            <td>${cmd.workflow}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  ` : ''

  const skillsSection = `
    <div class="section-header">SKILLS</div>
    ${plugin.skills.map(skill => `
      <div class="skill-item">
        <div class="skill-name">${skill.name}</div>
        <div class="skill-desc">${skill.description}</div>
      </div>
    `).join('')}
  `

  const referencesSection = plugin.references.length > 0 ? `
    <div class="section-header">REFERENCES</div>
    <ul class="ref-list">
      ${plugin.references.map(ref => `
        <li><a href="${ref.url}" target="_blank" rel="noopener">${ref.label}</a></li>
      `).join('')}
    </ul>
  ` : ''

  return `
    <div class="page-header">
      <div class="page-title-row">
        <h1>${plugin.name}</h1>
        <span class="badge">${plugin.version}</span>
      </div>
      <p class="plugin-description">${plugin.description}</p>
    </div>

    <div class="install-block">
      <span class="install-label">INSTALL</span>
      <span class="install-cmd">${plugin.install}</span>
    </div>

    ${commandsSection}
    ${skillsSection}
    ${referencesSection}
  `
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- src/pages/plugin.test.js
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/plugin.js web/src/pages/plugin.test.js
git commit -m "feat(web): add plugin detail page renderer with tests"
```

---

## Task 6: Router + App Bootstrap

**Files:**
- Create: `web/src/main.js`
- Create: `web/src/main.test.js`

- [ ] **Step 1: Write the failing test**

Create `web/src/main.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { resolveRoute } from './main.js'
import { plugins } from './data/plugins.js'

describe('resolveRoute', () => {
  it('returns { page: "home" } for empty hash', () => {
    expect(resolveRoute('', plugins)).toEqual({ page: 'home' })
  })

  it('returns { page: "home" } for "#" hash', () => {
    expect(resolveRoute('#', plugins)).toEqual({ page: 'home' })
  })

  it('returns { page: "plugin", plugin } for known plugin hash', () => {
    const result = resolveRoute('#dataform-toolkit', plugins)
    expect(result.page).toBe('plugin')
    expect(result.plugin.id).toBe('dataform-toolkit')
  })

  it('returns { page: "plugin", plugin } for stl-generator-toolkit', () => {
    const result = resolveRoute('#stl-generator-toolkit', plugins)
    expect(result.page).toBe('plugin')
    expect(result.plugin.id).toBe('stl-generator-toolkit')
  })

  it('returns { page: "home" } for unknown hash', () => {
    expect(resolveRoute('#unknown-plugin', plugins)).toEqual({ page: 'home' })
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- src/main.test.js
```

Expected: FAIL — `main.js` does not exist or `resolveRoute` not exported.

- [ ] **Step 3: Create `web/src/main.js`**

```js
import { plugins } from './data/plugins.js'
import { renderHome } from './pages/home.js'
import { renderPlugin } from './pages/plugin.js'

/**
 * Pure routing function — maps a hash string to a route descriptor.
 * Exported for testing; not dependent on DOM.
 * @param {string} hash - e.g. "" or "#dataform-toolkit"
 * @param {Array} pluginList - the plugins array
 * @returns {{ page: 'home' } | { page: 'plugin', plugin: Object }}
 */
export function resolveRoute(hash, pluginList) {
  const id = hash.replace(/^#/, '')
  if (!id) return { page: 'home' }
  const plugin = pluginList.find(p => p.id === id)
  return plugin ? { page: 'plugin', plugin } : { page: 'home' }
}

function updateActiveNav(hash) {
  document.querySelectorAll('.nav-link').forEach(link => {
    const linkHash = link.getAttribute('data-hash')
    const currentId = hash.replace(/^#/, '')
    link.classList.toggle('active', linkHash === currentId)
  })
}

function render() {
  const hash = location.hash
  const route = resolveRoute(hash, plugins)
  const el = document.getElementById('main-content')

  if (route.page === 'plugin') {
    el.innerHTML = renderPlugin(route.plugin)
  } else {
    el.innerHTML = renderHome(plugins)
  }

  updateActiveNav(hash)
}

window.addEventListener('hashchange', render)
window.addEventListener('DOMContentLoaded', render)
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
npm test
```

Expected: All tests PASS (plugins, home, plugin, main).

- [ ] **Step 5: Commit**

```bash
git add web/src/main.js web/src/main.test.js
git commit -m "feat(web): add hash router and app bootstrap with tests"
```

---

## Task 7: Manual Integration Verification

No code changes — visual verification that the app works end-to-end.

- [ ] **Step 1: Start dev server**

```bash
cd web
npm run dev
```

Open `http://localhost:5173` in browser.

- [ ] **Step 2: Verify Overview page**

- Sidebar shows "Claude Plugins" brand, "Overview" link, and 3 plugin names under "PLUGINS"
- Main content shows 3 plugin cards with name, description, install command, and "View docs →" link
- "Overview" nav link is highlighted in indigo

- [ ] **Step 3: Verify dataform-toolkit detail page**

Click "dataform-toolkit" in sidebar (or "View docs →" from overview).

- URL hash changes to `#dataform-toolkit`
- Header shows plugin name + version badge
- Install block shows `/plugin install dataform-toolkit@ihistand`
- Commands table shows 4 rows: `/dataform-test`, `/dataform-deploy`, `/dataform-new-table`, `/dataform-etl`
- Skills section shows `dataform-engineering-fundamentals`
- References section shows 2 links
- "dataform-toolkit" nav link is highlighted in sidebar

- [ ] **Step 4: Verify acuantia-dataform detail page**

Click "acuantia-dataform" in sidebar.

- No "COMMANDS" section visible (commands array is empty)
- Skills section shows `acuantia-dataform`
- No "REFERENCES" section visible

- [ ] **Step 5: Verify production build**

```bash
npm run build
open dist/index.html
```

Expected: App loads correctly when opened from filesystem (not a dev server). Hash routing still works.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(web): claude-plugins docs web app complete"
```

---

## Summary

After all tasks complete:

- `npm run dev` — dev server at `http://localhost:5173`
- `npm test` — all unit tests pass
- `npm run build` — static build in `dist/`, works opened directly from filesystem

All 3 plugins are documented. `acuantia-dataform` correctly renders without a commands table.
