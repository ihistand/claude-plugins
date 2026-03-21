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
