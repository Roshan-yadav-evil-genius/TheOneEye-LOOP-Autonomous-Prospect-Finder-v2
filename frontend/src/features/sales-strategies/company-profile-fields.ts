/** Display order for CompanyProfile keys returned on CompanyDetail.profile. */
export const COMPANY_PROFILE_FIELDS = [
  { key: 'linkedin_company_url', label: 'LinkedIn company URL' },
  { key: 'industry', label: 'Industry' },
  { key: 'sub_industry', label: 'Sub-industry' },
  { key: 'headquarters', label: 'Headquarters' },
  { key: 'operating_countries', label: 'Operating countries' },
  { key: 'employee_count', label: 'Employee count' },
  { key: 'revenue_range', label: 'Revenue range' },
  { key: 'founded_year', label: 'Founded year' },
  { key: 'ownership', label: 'Ownership' },
  { key: 'business_model', label: 'Business model' },
  { key: 'description', label: 'Description' },
] as const

export type CompanyProfileFieldKey = (typeof COMPANY_PROFILE_FIELDS)[number]['key']

export function formatProfileValue(value: unknown): string {
  if (value == null || value === '') return '—'
  if (Array.isArray(value)) {
    return value.length === 0 ? '—' : value.map((item) => String(item)).join(', ')
  }
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
