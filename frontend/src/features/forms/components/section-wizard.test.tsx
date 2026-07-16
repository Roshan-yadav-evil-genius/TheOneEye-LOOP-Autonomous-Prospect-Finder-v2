import { fireEvent, render, screen } from '@testing-library/react'
import axe from 'axe-core'
import { describe, expect, it, vi } from 'vitest'

import { SectionWizard } from './section-wizard'

const overviewSection = {
  key: 'overview',
  title: 'Overview',
  help: 'Help',
  fields: [{ path: 'name', label: 'Name', kind: 'text' as const, required: true }],
}

describe('SectionWizard', () => {
  it('validates required fields and submits filled section values', async () => {
    const submit = vi.fn().mockResolvedValue(undefined)
    const { container } = render(
      <SectionWizard
        title="test"
        sections={[overviewSection]}
        initialValue={{ overview: { name: '' } }}
        onSubmit={submit}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Submit test' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Name is required')
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Value' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit test' }))
    expect(submit).toHaveBeenCalledWith({ overview: { name: 'Value' } })
    expect((await axe.run(container)).violations).toEqual([])
  })

  it('renders readonly sections without submit or edits', async () => {
    const submit = vi.fn().mockResolvedValue(undefined)
    const { container } = render(
      <SectionWizard
        title="test"
        sections={[
          overviewSection,
          {
            key: 'targets',
            title: 'Targets',
            help: 'Targets help',
            fields: [{ path: 'count', label: 'Count', kind: 'number' }],
          },
        ]}
        initialValue={{ overview: { name: 'Seeded strategy' }, targets: { count: 3 } }}
        readOnly
        onSubmit={submit}
      />,
    )

    const nameField = container.querySelector('input[type="text"]')
    expect(nameField).toHaveValue('Seeded strategy')
    expect(nameField).toBeDisabled()
    expect(container.querySelector('button.button--primary')?.textContent).toBe('Next')
    expect(screen.getByText(/Read-only snapshot/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByRole('heading', { name: /2\. Targets/i })).toBeInTheDocument()
    expect(submit).not.toHaveBeenCalled()
    expect((await axe.run(container)).violations).toEqual([])
  })

  it('labels intermediate steps as Continue instead of Save and continue', () => {
    render(
      <SectionWizard
        title="test"
        sections={[
          overviewSection,
          {
            key: 'targets',
            title: 'Targets',
            help: 'Targets help',
            fields: [{ path: 'count', label: 'Count', kind: 'number' }],
          },
        ]}
        initialValue={{ overview: { name: 'Seeded' }, targets: { count: 3 } }}
        onSubmit={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Save & continue/i })).not.toBeInTheDocument()
  })
})
