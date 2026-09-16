import { describe, it, expect } from 'vitest'
import { renderPlugin } from './plugin.js'
import { plugins } from '../data/plugins.js'

const sqlanvil = plugins.find(p => p.id === 'sqlanvil-toolkit')
const acuantia = plugins.find(p => p.id === 'acuantia-dataform')
const stl = plugins.find(p => p.id === 'stl-generator-toolkit')

describe('renderPlugin', () => {
  it('returns a string', () => {
    expect(typeof renderPlugin(sqlanvil)).toBe('string')
  })

  it('renders plugin name and version', () => {
    const html = renderPlugin(sqlanvil)
    expect(html).toContain('sqlanvil-toolkit')
    expect(html).toContain(sqlanvil.version)
  })

  it('renders install command', () => {
    const html = renderPlugin(sqlanvil)
    expect(html).toContain('/plugin install sqlanvil-toolkit@ihistand')
  })

  it('renders commands table when commands exist', () => {
    const html = renderPlugin(sqlanvil)
    expect(html).toContain('/sqlanvil-compile')
    expect(html).toContain('/sqlanvil-test')
    expect(html).toContain('/sqlanvil-run')
    expect(html).toContain('/sqlanvil-new-table')
  })

  it('omits commands section when commands array is empty', () => {
    const html = renderPlugin(acuantia)
    expect(html).not.toContain('commands-table')
    expect(html).not.toContain('COMMANDS')
  })

  it('renders skills section', () => {
    const html = renderPlugin(sqlanvil)
    expect(html).toContain('sqlanvil-engineering-fundamentals')
  })

  it('renders references when present', () => {
    const html = renderPlugin(sqlanvil)
    expect(html).toContain('SQLAnvil Docs')
    expect(html).toContain('https://sqlanvil.com/docs/')
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
