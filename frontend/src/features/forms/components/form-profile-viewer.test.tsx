import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { FormSectionDefinition } from '../form-field-schema'
import { FormProfileViewer } from './form-profile-viewer'

const sections: FormSectionDefinition[] = [
  {
    key: 'identity',
    title: 'Organization identity',
    help: 'Basic record fields.',
    fields: [
      { path: 'thumbnail_url', label: 'Thumbnail / Logo', kind: 'file', help: 'Upload an image' },
      { path: 'name', label: 'Organization name', kind: 'text', required: true, help: 'Legal name' },
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
  {
    key: 'case_studies',
    title: 'Case studies',
    help: 'Notable projects.',
    fields: [
      {
        path: '.',
        label: 'Case studies',
        kind: 'object-list',
        itemFields: [
          { path: 'title', label: 'Title', kind: 'text' },
          { path: 'outcome', label: 'Outcome', kind: 'textarea' },
        ],
      },
    ],
  },
]

describe('FormProfileViewer', () => {
  it('renders every section and field value read-only', () => {
    render(
      <MemoryRouter>
        <FormProfileViewer
          title="Organization profile"
          validated
          sections={sections}
          value={{
            identity: { name: 'Acme', website: 'https://acme.example' },
            industry: { primary: 'Software', secondary: ['SaaS', 'B2B'] },
          }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Organization profile' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Organization identity' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Industry' })).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.getByText(/https:\/\/acme\.example/)).toBeInTheDocument()
    expect(screen.getByText('Software')).toBeInTheDocument()
    expect(screen.getByText('SaaS')).toBeInTheDocument()
    expect(screen.getByText('B2B')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('separates field label and help text into distinct elements', () => {
    render(
      <MemoryRouter>
        <FormProfileViewer
          title="Profile"
          validated
          sections={sections}
          value={{ identity: { name: 'Acme' } }}
        />
      </MemoryRouter>,
    )

    const labelSpan = screen.getByText('Organization name')
    const helpSpan = screen.getByText('Legal name')

    expect(labelSpan).toHaveClass('field-value-display__label')
    expect(helpSpan).toHaveClass('field-value-display__help')
  })

  it('renders image previews when image/logo fields contain a valid URL', () => {
    render(
      <MemoryRouter>
        <FormProfileViewer
          title="Profile"
          validated
          sections={sections}
          value={{ identity: { thumbnail_url: '/static/uploads/logo.png' } }}
        />
      </MemoryRouter>,
    )

    const img = screen.getByRole('img', { name: 'Thumbnail / Logo' })
    expect(img).toHaveAttribute('src', '/static/uploads/logo.png')
    expect(screen.getByText('View image ↗')).toBeInTheDocument()
  })

  it('renders object lists inside sub-cards with titles and badges', () => {
    render(
      <MemoryRouter>
        <FormProfileViewer
          title="Profile"
          validated
          sections={sections}
          value={{
            case_studies: [
              { title: 'Project Titan', outcome: 'Increased ARR by 40%' },
              { title: 'Project Apollo', outcome: 'Reduced latency by 50%' },
            ],
          }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Project Titan' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Project Apollo' })).toBeInTheDocument()
    expect(screen.getByText('#1')).toBeInTheDocument()
    expect(screen.getByText('#2')).toBeInTheDocument()
    expect(screen.getByText('Increased ARR by 40%')).toBeInTheDocument()
  })

  it('renders quick section edit buttons when getEditUrl is provided', () => {
    render(
      <MemoryRouter>
        <FormProfileViewer
          title="Profile"
          validated
          sections={sections}
          value={{ identity: { name: 'Acme' } }}
          getEditUrl={(key) => `/orgs/123/edit?step=${key}`}
        />
      </MemoryRouter>,
    )

    const editLinks = screen.getAllByRole('link', { name: /Edit/ })
    expect(editLinks.length).toBeGreaterThan(0)
    expect(editLinks[0]).toHaveAttribute('href', '/orgs/123/edit?step=identity')
  })
})

