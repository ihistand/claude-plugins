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

  el.scrollTop = 0
  updateActiveNav(hash)
}

if (typeof window !== 'undefined') {
  window.addEventListener('hashchange', render)
  window.addEventListener('DOMContentLoaded', render)
}
