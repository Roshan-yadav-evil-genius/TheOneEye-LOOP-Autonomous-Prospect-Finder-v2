import axe from 'axe-core'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { ThemeProvider } from './shared/hooks/theme-provider'

vi.mock('./features/system/api/system-api', () => ({
  getLiveness: async () => ({ service: 'loop-api', status: 'ok' }),
  getBuildInfo: async () => ({
    version: '0.1.0',
    commit_sha: 'test',
    build_timestamp: '2026-07-15T00:00:00Z',
  }),
}))

vi.mock('./features/organizations/api/organizations-api', () => ({
  organizationsApi: {
    listOrganizations: async () => [],
    getOrganization: async () => ({
      id: 'org-1',
      name: 'Acme',
      website: 'https://acme.example',
      primary_contact_email: null,
      org_form: {},
      profile_validated: true,
    }),
  },
}))

vi.mock('./features/admin/api/admin-api', () => ({
  adminApi: {
    jobs: async () => [],
    deadLetters: async () => [],
    audit: async () => [],
    schedules: async () => [],
  },
}))

vi.mock('./features/products/api/products-api', () => ({
  productsApi: {
    listProducts: async () => [],
  },
}))

vi.mock('./features/sales-strategies/api/sales-strategy-api', () => ({
  salesStrategyApi: {
    listStrategies: async () => [],
    processStatus: async () => null,
  },
}))

describe('accessibility', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('operator home has no serious axe violations', async () => {
    const { container } = render(
      <MemoryRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </MemoryRouter>,
    )
    const results = await axe.run(container)
    const serious = results.violations.filter(
      (item) => item.impact === 'serious' || item.impact === 'critical',
    )
    expect(serious).toEqual([])
  })
})
