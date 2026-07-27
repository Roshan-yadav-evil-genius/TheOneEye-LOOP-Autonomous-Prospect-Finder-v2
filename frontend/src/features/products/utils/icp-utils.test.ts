import { describe, expect, it } from 'vitest'
import { toProductFormValue } from './icp-utils'

describe('icp-utils', () => {
  it('merges nested ICP attributes with product template defaults', () => {
    const product = {
      name: 'Test Product',
      kind: 'product',
      icp_form: {
        icp: {
          industries: {
            primary: ['Software & SaaS', 'Technology Services'],
            secondary: ['Consulting Firms'],
            avoid: ['B2C Retail'],
          },
          company_size: {
            employees_min: 50,
            revenue_min: 1000000,
          },
          geography: {
            countries: ['United States', 'India'],
            regions: ['North America'],
          },
          maturity: ['Series A+'],
        },
      },
    }

    const formVal = toProductFormValue(product) as any
    expect(formVal.identity.name).toBe('Test Product')
    expect(formVal.identity.kind).toBe('product')
    expect(formVal.icp.industries.primary).toEqual(['Software & SaaS', 'Technology Services'])
    expect(formVal.icp.industries.secondary).toEqual(['Consulting Firms'])
    expect(formVal.icp.industries.avoid).toEqual(['B2C Retail'])
    expect(formVal.icp.company_size.employees_min).toBe(50)
    expect(formVal.icp.company_size.revenue_min).toBe(1000000)
    expect(formVal.icp.geography.countries).toEqual(['United States', 'India'])
    expect(formVal.icp.geography.regions).toEqual(['North America'])
    expect(formVal.icp.maturity).toEqual(['Series A+'])
  })

  it('preserves entity identity name and kind even if icp_form has empty identity', () => {
    const product = {
      name: 'Cloud Platform',
      kind: 'service',
      icp_form: {
        identity: {},
      },
    }

    const formVal = toProductFormValue(product) as any
    expect(formVal.identity.name).toBe('Cloud Platform')
    expect(formVal.identity.kind).toBe('service')
  })
})
