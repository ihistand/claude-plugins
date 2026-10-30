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

  it('prd-toolkit has 4 commands', () => {
    const prd = plugins.find(p => p.id === 'prd-toolkit')
    expect(prd.commands.map(c => c.name)).toEqual(['/prd-new', '/prd-adopt', '/prd-change', '/prd-context'])
    expect(prd.version).toBe('0.3.0')
    expect(prd.description).toContain('/prd-context')
  })

  it('prd-toolkit dry-runs with prd-tester and links the design specs', () => {
    const prd = plugins.find(p => p.id === 'prd-toolkit')
    const prdNew = prd.commands.find(c => c.name === '/prd-new')
    expect(prdNew.workflow).toContain('prd-tester dry run')
    expect(prdNew.workflow).not.toContain('fresh-agent')
    const urls = prd.references.map(r => r.url)
    expect(urls.some(u => u.endsWith('/2026-10-29-prd-toolkit-design.md'))).toBe(true)
    expect(urls.some(u => u.endsWith('/2026-10-29-prd-toolkit-0.2-design.md'))).toBe(true)
    expect(urls.some(u => u.endsWith('/2026-10-30-prd-toolkit-0.3-design.md'))).toBe(true)
  })

  it('plugin ids match known routes', () => {
    const ids = plugins.map(p => p.id)
    expect(ids).toContain('sqlanvil-toolkit')
    expect(ids).toContain('stl-generator-toolkit')
    expect(ids).toContain('prd-toolkit')
  })
})
