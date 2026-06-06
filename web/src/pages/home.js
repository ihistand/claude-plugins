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
      <a href="#${p.id}" class="plugin-card-link">View docs &rarr;</a>
    </div>
  `).join('')

  return `
    <div class="content-inner">
      <div class="page-header">
        <h1>Claude Plugins</h1>
        <p class="plugin-description">Developer documentation for the ihistand plugin marketplace.</p>
      </div>
      <div class="setup-block">
        <p class="setup-label">One-time setup — add the marketplace, then install any plugin below:</p>
        <code class="setup-cmd">/plugin marketplace add ihistand/claude-plugins</code>
      </div>
      ${cards}
      <div class="extend-section">
        <h2>Extend a skill for your team</h2>
        <p>Skills layer. You can write a thin, org-specific skill on top of a base
        skill: it names the base as a required prerequisite and adds only your own
        conventions, without repeating the generic rules.</p>
        <p><strong>acuantia-dataform</strong> is a worked example — it extends
        <code>dataform-engineering-fundamentals</code> with one team's ODS two-argument
        <code>ref()</code> syntax, <code>looker_</code> filename conventions, and
        cross-project coordination. Do the same on top of
        <code>sqlanvil-engineering-fundamentals</code> for your own Postgres/Supabase
        standards.</p>
      </div>
    </div>
  `
}
