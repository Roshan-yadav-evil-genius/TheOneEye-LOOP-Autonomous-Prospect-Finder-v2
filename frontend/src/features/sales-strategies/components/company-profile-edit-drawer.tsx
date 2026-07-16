import { useEffect, useState } from 'react'

import { Button } from '../../../shared/components/button'
import { Drawer } from '../../../shared/components/drawer'
import { FormField } from '../../../shared/components/form-field'
import {
  COMPANY_PROFILE_FIELDS,
  type CompanyProfileFieldKey,
} from '../company-profile-fields'

type ProfileDraft = Record<string, unknown>

const LIST_FIELDS = new Set<CompanyProfileFieldKey>(['operating_countries'])
const TEXTAREA_FIELDS = new Set<CompanyProfileFieldKey>(['description'])
const NUMBER_FIELDS = new Set<CompanyProfileFieldKey>(['founded_year', 'employee_count'])

function draftFromProfile(profile: Record<string, unknown> | null): ProfileDraft {
  const draft: ProfileDraft = {}
  for (const { key } of COMPANY_PROFILE_FIELDS) {
    const value = profile?.[key]
    if (LIST_FIELDS.has(key)) {
      draft[key] = Array.isArray(value) ? value.join('\n') : ''
      continue
    }
    draft[key] = value ?? ''
  }
  return draft
}

function profileFromDraft(draft: ProfileDraft): Record<string, unknown> {
  const profile: Record<string, unknown> = {}
  for (const { key } of COMPANY_PROFILE_FIELDS) {
    const raw = draft[key]
    if (LIST_FIELDS.has(key)) {
      const items =
        typeof raw === 'string'
          ? raw
              .split('\n')
              .map((item) => item.trim())
              .filter(Boolean)
          : []
      if (items.length > 0) profile[key] = items
      continue
    }
    if (NUMBER_FIELDS.has(key)) {
      if (raw === '' || raw == null) continue
      const parsed = Number(raw)
      if (!Number.isNaN(parsed)) profile[key] = parsed
      continue
    }
    if (typeof raw === 'string' && raw.trim()) {
      profile[key] = raw.trim()
    }
  }
  return profile
}

const FIELD_HELP: Partial<Record<CompanyProfileFieldKey, string>> = {
  linkedin_company_url: 'Canonical LinkedIn company page URL, e.g. https://www.linkedin.com/company/acme',
  industry: 'Primary industry label shown to operators and agents.',
  sub_industry: 'More specific industry niche when known.',
  headquarters: 'City and country, e.g. Austin, US.',
  operating_countries: 'One country per line.',
  employee_count: 'Approximate headcount or range, e.g. 201–500.',
  revenue_range: 'Approximate annual revenue band.',
  founded_year: 'Four-digit year the company was founded.',
  ownership: 'Ownership type, e.g. private, public, PE-backed.',
  business_model: 'How the company makes money, e.g. B2B SaaS.',
  description: 'Short firmographic summary agents can cite in outreach.',
}

export function CompanyProfileEditDrawer({
  open,
  onOpenChange,
  profile,
  saving,
  onSave,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  profile: Record<string, unknown> | null
  saving?: boolean
  onSave: (profile: Record<string, unknown>) => Promise<void>
}) {
  const [draft, setDraft] = useState<ProfileDraft>(() => draftFromProfile(profile))

  useEffect(() => {
    if (open) setDraft(draftFromProfile(profile))
  }, [open, profile])

  const updateField = (key: CompanyProfileFieldKey, value: string) => {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  return (
    <Drawer
      open={open}
      onOpenChange={onOpenChange}
      title="Edit enriched profile"
      description="Update firmographics for this company. Changes apply to the global company record."
      footer={
        <Button
          disabled={saving}
          onClick={() => void onSave(profileFromDraft(draft))}
        >
          {saving ? 'Saving…' : 'Save profile'}
        </Button>
      }
    >
      <div className="field-grid">
        {COMPANY_PROFILE_FIELDS.map(({ key, label }) => (
          <FormField key={key} label={label} help={FIELD_HELP[key]}>
            {TEXTAREA_FIELDS.has(key) || LIST_FIELDS.has(key) ? (
              <textarea
                className="control"
                rows={LIST_FIELDS.has(key) ? 3 : 4}
                value={String(draft[key] ?? '')}
                onChange={(event) => updateField(key, event.target.value)}
              />
            ) : NUMBER_FIELDS.has(key) ? (
              <input
                className="control"
                type="number"
                value={String(draft[key] ?? '')}
                onChange={(event) => updateField(key, event.target.value)}
              />
            ) : (
              <input
                className="control"
                value={String(draft[key] ?? '')}
                onChange={(event) => updateField(key, event.target.value)}
              />
            )}
          </FormField>
        ))}
      </div>
    </Drawer>
  )
}
