import { describe, it, expect, beforeEach } from 'vitest'
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
