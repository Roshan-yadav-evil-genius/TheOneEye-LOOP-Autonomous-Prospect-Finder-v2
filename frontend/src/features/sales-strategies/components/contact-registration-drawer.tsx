import { useState } from 'react'

import { Button } from '../../../shared/components/button'
import { Drawer } from '../../../shared/components/drawer'
import { FormField } from '../../../shared/components/form-field'
import type { RegisterContactRequest } from '../api/sales-strategy-api'

const initialDraft: RegisterContactRequest = {
  full_name: '',
  job_title: '',
  department: '',
  seniority: '',
  linkedin_url: '',
  public_email: '',
  public_phone: '',
  location: '',
  selection_reason: '',
  fit_rationale: '',
  confidence_score: 80,
  evidence_urls: [],
}

function parseEvidenceUrls(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function ContactRegistrationDrawer({
  open,
  onOpenChange,
  saving,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  saving?: boolean
  onSubmit: (payload: RegisterContactRequest) => Promise<void>
}) {
  const [draft, setDraft] = useState<RegisterContactRequest>(initialDraft)
  const [evidenceText, setEvidenceText] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const reset = () => {
    setDraft(initialDraft)
    setEvidenceText('')
    setLocalError(null)
  }

  const handleOpenChange = (next: boolean) => {
    if (!next) reset()
    onOpenChange(next)
  }

  const submit = async () => {
    if (!draft.full_name.trim()) {
      setLocalError('Full name is required.')
      return
    }
    if (!draft.job_title.trim()) {
      setLocalError('Job title is required.')
      return
    }
    if (!draft.linkedin_url.trim()) {
      setLocalError('LinkedIn URL is required.')
      return
    }
    if (!draft.selection_reason.trim()) {
      setLocalError('Selection reason is required.')
      return
    }
    if (!draft.fit_rationale.trim()) {
      setLocalError('Fit rationale is required.')
      return
    }
    if (draft.confidence_score < 0 || draft.confidence_score > 100) {
      setLocalError('Confidence score must be between 0 and 100.')
      return
    }
    setLocalError(null)
    await onSubmit({
      ...draft,
      full_name: draft.full_name.trim(),
      job_title: draft.job_title.trim(),
      linkedin_url: draft.linkedin_url.trim(),
      selection_reason: draft.selection_reason.trim(),
      fit_rationale: draft.fit_rationale.trim(),
      department: draft.department?.trim() || null,
      seniority: draft.seniority?.trim() || null,
      public_email: draft.public_email?.trim() || null,
      public_phone: draft.public_phone?.trim() || null,
      location: draft.location?.trim() || null,
      evidence_urls: parseEvidenceUrls(evidenceText),
    })
    reset()
  }

  return (
    <Drawer
      open={open}
      onOpenChange={handleOpenChange}
      title="Register contact"
      description="Add a prospect to this company for the active sales strategy."
      footer={
        <Button disabled={saving} onClick={() => void submit()}>
          {saving ? 'Registering…' : 'Register contact'}
        </Button>
      }
    >
      <div className="field-grid">
        <FormField label="Full name" help="Prospect's display name as shown on LinkedIn.">
          <input
            className="control"
            value={draft.full_name}
            onChange={(event) => setDraft({ ...draft, full_name: event.target.value })}
          />
        </FormField>
        <FormField label="Job title" help="Current role at the company.">
          <input
            className="control"
            value={draft.job_title}
            onChange={(event) => setDraft({ ...draft, job_title: event.target.value })}
          />
        </FormField>
        <FormField label="Department" help="Optional department or function.">
          <input
            className="control"
            value={draft.department ?? ''}
            onChange={(event) => setDraft({ ...draft, department: event.target.value })}
          />
        </FormField>
        <FormField label="Seniority" help="Optional seniority band, e.g. VP or Director.">
          <input
            className="control"
            value={draft.seniority ?? ''}
            onChange={(event) => setDraft({ ...draft, seniority: event.target.value })}
          />
        </FormField>
        <FormField
          label="LinkedIn URL"
          help="Canonical LinkedIn /in/ profile URL — required to associate the contact."
        >
          <input
            className="control"
            value={draft.linkedin_url}
            onChange={(event) => setDraft({ ...draft, linkedin_url: event.target.value })}
          />
        </FormField>
        <FormField label="Public email" help="Optional work email if publicly listed.">
          <input
            className="control"
            type="email"
            value={draft.public_email ?? ''}
            onChange={(event) => setDraft({ ...draft, public_email: event.target.value })}
          />
        </FormField>
        <FormField label="Public phone" help="Optional phone number if publicly listed.">
          <input
            className="control"
            value={draft.public_phone ?? ''}
            onChange={(event) => setDraft({ ...draft, public_phone: event.target.value })}
          />
        </FormField>
        <FormField label="Location" help="City, region, or country when known.">
          <input
            className="control"
            value={draft.location ?? ''}
            onChange={(event) => setDraft({ ...draft, location: event.target.value })}
          />
        </FormField>
        <FormField
          label="Selection reason"
          help="Why this contact was chosen for outreach on this strategy."
        >
          <textarea
            className="control"
            rows={2}
            value={draft.selection_reason}
            onChange={(event) => setDraft({ ...draft, selection_reason: event.target.value })}
          />
        </FormField>
        <FormField
          label="Fit rationale"
          help="How this contact matches the strategy ICP and buyer personas."
        >
          <textarea
            className="control"
            rows={2}
            value={draft.fit_rationale}
            onChange={(event) => setDraft({ ...draft, fit_rationale: event.target.value })}
          />
        </FormField>
        <FormField label="Confidence score" help="Fit confidence from 0 to 100.">
          <input
            className="control"
            type="number"
            min={0}
            max={100}
            value={draft.confidence_score}
            onChange={(event) =>
              setDraft({ ...draft, confidence_score: Number(event.target.value) })
            }
          />
        </FormField>
        <FormField label="Evidence URLs" help="One supporting URL per line (LinkedIn posts, bios, etc.).">
          <textarea
            className="control"
            rows={3}
            value={evidenceText}
            onChange={(event) => setEvidenceText(event.target.value)}
          />
        </FormField>
        {localError ? <p role="alert" className="error-banner">{localError}</p> : null}
      </div>
    </Drawer>
  )
}
