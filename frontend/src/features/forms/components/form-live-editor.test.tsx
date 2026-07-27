import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { FormLiveEditor } from './form-live-editor'
import type { FormSectionDefinition } from '../form-field-schema'
import * as exportModule from '../lib/export-filled-markdown'
import { formsApi } from '../api/forms-api'

const sampleSections: FormSectionDefinition[] = [
  {
    key: 'identity',
    title: 'Organization Identity',
    fields: [
      { path: 'name', label: 'Organization Name', kind: 'text' },
    ],
  },
]

describe('FormLiveEditor download buttons', () => {
  it('renders Download Template and Export Filled Markdown buttons before Save Changes', () => {
    render(
      <FormLiveEditor
        title="Organization Form"
        sections={sampleSections}
        initialValue={{ identity: { name: 'Acme' } }}
        onSubmit={async () => {}}
      />
    )

    const downloadTemplateBtn = screen.getByRole('button', { name: 'Download Template' })
    const exportFilledBtn = screen.getByRole('button', { name: 'Export Filled Markdown' })
    const saveBtn = screen.getByRole('button', { name: 'Save Changes' })

    expect(downloadTemplateBtn).toBeInTheDocument()
    expect(exportFilledBtn).toBeInTheDocument()
    expect(saveBtn).toBeInTheDocument()
  })

  it('triggers exportFilledMarkdown when Export Filled Markdown is clicked', () => {
    const spy = vi.spyOn(exportModule, 'exportFilledMarkdown').mockImplementation(() => {})

    render(
      <FormLiveEditor
        title="Organization Form"
        sections={sampleSections}
        initialValue={{ identity: { name: 'Acme' } }}
        onSubmit={async () => {}}
      />
    )

    const exportFilledBtn = screen.getByRole('button', { name: 'Export Filled Markdown' })
    fireEvent.click(exportFilledBtn)

    expect(spy).toHaveBeenCalledWith('Organization Form', sampleSections, { identity: { name: 'Acme' } })
    spy.mockRestore()
  })

  it('triggers formsApi.downloadTemplate when Download Template is clicked', async () => {
    const spy = vi.spyOn(formsApi, 'downloadTemplate').mockResolvedValue({
      filename: 'organization-template.md',
      content: '# Template',
    })

    render(
      <FormLiveEditor
        formKey="organization"
        title="Organization Form"
        sections={sampleSections}
        initialValue={{ identity: { name: 'Acme' } }}
        onSubmit={async () => {}}
      />
    )

    const downloadTemplateBtn = screen.getByRole('button', { name: 'Download Template' })
    fireEvent.click(downloadTemplateBtn)

    expect(spy).toHaveBeenCalledWith('organization')
    spy.mockRestore()
  })
})
