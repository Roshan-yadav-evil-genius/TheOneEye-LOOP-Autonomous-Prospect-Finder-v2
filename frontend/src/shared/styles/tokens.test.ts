import { readFileSync } from 'fs'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'
import { describe, expect, it } from 'vitest'

const here = dirname(fileURLToPath(import.meta.url))

describe('design tokens', () => {
  it('defines LOOP visual CSS variables from the design-system plan', () => {
    const css = readFileSync(resolve(here, 'tokens.css'), 'utf8')
    for (const token of [
      '--color-bg-primary',
      '--color-text-primary',
      '--color-accent-primary',
      '--color-border-default',
      '--color-control-bg',
      '--color-control-border',
      '--color-control-border-hover',
      '--color-control-placeholder',
      '--radius-md',
      '--shadow-panel',
    ]) {
      expect(css).toContain(token)
    }
  })
})
