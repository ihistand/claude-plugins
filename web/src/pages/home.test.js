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

  it('shows the one-time marketplace-add setup step', () => {
    expect(html).toContain('/plugin marketplace add ihistand/claude-plugins')
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
    expect(html).toContain('#sqlanvil-toolkit')
    expect(html).toContain('#stl-generator-toolkit')
    expect(html).toContain('#acuantia-dataform')
  })

  it('renders a version badge for every plugin', () => {
    const versions = html.match(/\d+\.\d+\.\d+/g) || []
    expect(versions.length).toBeGreaterThanOrEqual(plugins.length)
  })

  it('renders the "extend a skill" section citing acuantia', () => {
    expect(html).toContain('Extend a skill for your team')
    expect(html).toContain('acuantia-dataform')
    expect(html).toContain('sqlanvil-engineering-fundamentals')
  })
})
