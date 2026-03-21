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
