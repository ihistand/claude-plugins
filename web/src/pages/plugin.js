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
