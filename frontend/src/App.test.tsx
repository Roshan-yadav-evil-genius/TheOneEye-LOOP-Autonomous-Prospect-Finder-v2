import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

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
  },
}))

vi.mock('./features/admin/api/admin-api', () => ({
  adminApi: {
    jobs: async () => [],
    deadLetters: async () => [],
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

describe('App', () => {
  it('renders the operator home', () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /LOOP operator home/i })).toBeInTheDocument()
  })
})
