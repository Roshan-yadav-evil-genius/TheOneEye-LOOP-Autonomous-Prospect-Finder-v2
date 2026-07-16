import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CompanyProfileSection } from './company-profile-section'

describe('CompanyProfileSection', () => {
  it('shows all enrichment fields as empty when profile is null', () => {
    render(<CompanyProfileSection profile={null} />)
    expect(screen.getByRole('heading', { name: 'Enriched profile' })).toBeInTheDocument()
    expect(screen.getByText('Industry')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(11)
    expect(screen.queryByText('No enriched profile yet')).not.toBeInTheDocument()
  })

  it('renders labeled firmographic fields as key-value pairs', () => {
    render(
      <CompanyProfileSection
        profile={{
          linkedin_company_url: 'https://www.linkedin.com/company/acme',
          industry: 'Software',
          sub_industry: 'B2B SaaS',
          headquarters: 'Austin, TX',
          operating_countries: ['US', 'CA'],
          employee_count: '51-200',
          revenue_range: '$10M-$25M',
          founded_year: 2018,
          ownership: 'Private',
          business_model: 'B2B SaaS',
          description: 'Mid-market SaaS platform.',
          custom_signal: 'Hiring SDRs',
        }}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Enriched profile' })).toBeInTheDocument()
    expect(screen.getByText('Industry')).toBeInTheDocument()
    expect(screen.getByText('Software')).toBeInTheDocument()
    expect(screen.getByText('US')).toBeInTheDocument()
    expect(screen.getByText('CA')).toBeInTheDocument()
    expect(screen.getByText('Custom Signal')).toBeInTheDocument()
    expect(screen.getByText('Hiring SDRs')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /linkedin\.com\/company\/acme/i })).toHaveAttribute(
      'href',
      'https://www.linkedin.com/company/acme',
    )
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })
})
