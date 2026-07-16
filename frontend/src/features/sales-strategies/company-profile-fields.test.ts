import { describe, expect, it } from 'vitest'

import { formatProfileValue } from './company-profile-fields'

describe('formatProfileValue', () => {
  it('formats empty and scalar values', () => {
    expect(formatProfileValue(null)).toBe('—')
    expect(formatProfileValue('')).toBe('—')
    expect(formatProfileValue('SaaS')).toBe('SaaS')
    expect(formatProfileValue(2014)).toBe('2014')
  })

  it('joins arrays and stringifies unexpected objects', () => {
    expect(formatProfileValue(['US', 'CA'])).toBe('US, CA')
    expect(formatProfileValue([])).toBe('—')
    expect(formatProfileValue({ nested: true })).toBe('{"nested":true}')
  })
})
