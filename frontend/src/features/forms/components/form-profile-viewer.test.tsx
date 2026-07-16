import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { FormSectionDefinition } from '../form-field-schema'
import { FormProfileViewer } from './form-profile-viewer'

const sections: FormSectionDefinition[] = [
  {
    key: 'identity',
    title: 'Organization identity',
    help: 'Basic record fields.',
    fields: [
      { path: 'name', label: 'Organization name', kind: 'text', required: true },
      { path: 'website', label: 'Website', kind: 'text' },
    ],
  },
  {
    key: 'industry',
    title: 'Industry',
    help: 'Industries served.',
    fields: [
      { path: 'primary', label: 'Primary industry', kind: 'text' },
      { path: 'secondary', label: 'Secondary industries', kind: 'string-list' },
    ],
  },
]

describe('FormProfileViewer', () => {
  it('renders every section and field value read-only', () => {
    render(
      <FormProfileViewer
        title="Organization profile"
        validated
        sections={sections}
        value={{
          identity: { name: 'Acme', website: 'https://acme.example' },
          industry: { primary: 'Software', secondary: ['SaaS', 'B2B'] },
        }}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Organization profile' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Organization identity' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Industry' })).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.getByText('https://acme.example')).toBeInTheDocument()
    expect(screen.getByText('Software')).toBeInTheDocument()
    expect(screen.getByText('SaaS')).toBeInTheDocument()
    expect(screen.getByText('B2B')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })
})
