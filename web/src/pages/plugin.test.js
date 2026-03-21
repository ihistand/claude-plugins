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
