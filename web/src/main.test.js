import { describe, it, expect } from 'vitest'
import { resolveRoute } from './main.js'
import { plugins } from './data/plugins.js'

describe('resolveRoute', () => {
  it('returns { page: "home" } for empty hash', () => {
    expect(resolveRoute('', plugins)).toEqual({ page: 'home' })
  })

  it('returns { page: "home" } for "#" hash', () => {
    expect(resolveRoute('#', plugins)).toEqual({ page: 'home' })
  })

  it('returns { page: "plugin", plugin } for known plugin hash', () => {
    const result = resolveRoute('#dataform-toolkit', plugins)
    expect(result.page).toBe('plugin')
    expect(result.plugin.id).toBe('dataform-toolkit')
  })

  it('returns { page: "plugin", plugin } for stl-generator-toolkit', () => {
    const result = resolveRoute('#stl-generator-toolkit', plugins)
    expect(result.page).toBe('plugin')
    expect(result.plugin.id).toBe('stl-generator-toolkit')
  })

  it('returns { page: "home" } for unknown hash', () => {
    expect(resolveRoute('#unknown-plugin', plugins)).toEqual({ page: 'home' })
  })
})
