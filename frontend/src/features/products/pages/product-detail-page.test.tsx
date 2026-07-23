import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProductDetailPage } from './product-detail-page'
import { useProductDetailStore } from '../stores/product-detail-store'
import { useStrategiesListStore } from '../../sales-strategies/stores/strategies-list-store'

vi.mock('../stores/product-detail-store', () => ({
  useProductDetailStore: vi.fn(),
}))

vi.mock('../../sales-strategies/stores/strategies-list-store', () => ({
  useStrategiesListStore: vi.fn(),
}))

const product = {
  id: 'prod-1',
  organization_id: 'org-1',
  name: 'Loop Outreach',
  kind: 'service',
  icp_form: { form_version: '2.0' },
  profile_validated: true,
}

describe('ProductDetailPage', () => {
  beforeEach(() => {
    vi.mocked(useProductDetailStore).mockReturnValue({
      product,
      loading: false,
      submitting: false,
      error: null,
      saved: false,
      load: vi.fn().mockResolvedValue(undefined),
      save: vi.fn().mockResolvedValue(undefined),
      reset: vi.fn(),
    })
    vi.mocked(useStrategiesListStore).mockReturnValue({
      strategies: [
        {
          id: 'strat-1',
          name: 'Enterprise push',
          company_finder_attempt: 0,
          target_companies: 10,
          contacts_per_company_default: 3,
        },
      ],
      loading: false,
      error: null,
      load: vi.fn().mockResolvedValue(undefined),
    })
  })

  it('defaults to Strategies and lists strategies', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/orgs/org-1/products/prod-1']}>
        <Routes>
          <Route path="/orgs/:orgId/products/:productId" element={<ProductDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('tab', { name: 'Details' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Strategies' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Add sales strategy' })).toHaveAttribute(
      'href',
      '/orgs/org-1/products/prod-1/sales-strategies/new',
    )
    expect(screen.getByRole('link', { name: 'Open Enterprise push' })).toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'Details' }))
    expect(await screen.findByRole('heading', { name: 'Product profile' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Product identity/i })).toBeInTheDocument()
    expect(screen.getByText('service')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit profile' })).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('redirects to edit page from list mode query param', () => {
    render(
      <MemoryRouter initialEntries={['/orgs/org-1/products/prod-1?tab=details&mode=edit']}>
        <Routes>
          <Route path="/orgs/:orgId/products/:productId" element={<ProductDetailPage />} />
          <Route path="/orgs/:orgId/products/:productId/edit" element={<div>Product Edit Page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Product Edit Page')).toBeInTheDocument()
  })
})
