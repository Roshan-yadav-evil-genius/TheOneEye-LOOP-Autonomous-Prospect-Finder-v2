import { Button } from '../../../shared/components/button'
import {
  COMPANY_PROFILE_FIELDS,
  formatProfileValue,
} from '../company-profile-fields'

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function ProfileValue({
  fieldKey,
  value,
}: {
  fieldKey: string
  value: unknown
}) {
  const display = formatProfileValue(value)
  const isUrl =
    fieldKey === 'linkedin_company_url' &&
    typeof value === 'string' &&
    value.startsWith('http')

  if (isUrl) {
    return (
      <a href={value} target="_blank" rel="noreferrer">
        {value}
      </a>
    )
  }

  if (Array.isArray(value) && value.length > 0) {
    return (
      <ul className="field-value-display__list">
        {value.map((item) => (
          <li key={String(item)}>{String(item)}</li>
        ))}
      </ul>
    )
  }

  return <>{display}</>
}

/**
 * Read-only firmographics from CompanyProfile — always shows all known fields.
 * Missing profile or empty values render as "—".
 */
export function CompanyProfileSection({
  profile,
  onEdit,
}: {
  profile: Record<string, unknown> | null
  onEdit?: () => void
}) {
  const data = profile ?? {}
  const knownKeys = new Set(COMPANY_PROFILE_FIELDS.map((field) => field.key))
  const extraEntries = Object.entries(data).filter(
    ([key, value]) =>
      !knownKeys.has(key as (typeof COMPANY_PROFILE_FIELDS)[number]['key']) &&
      value != null &&
      value !== '',
  )

  const rows: Array<{ key: string; label: string; value: unknown }> = [
    ...COMPANY_PROFILE_FIELDS.map(({ key, label }) => ({
      key,
      label,
      value: data[key],
    })),
    ...extraEntries.map(([key, value]) => ({
      key,
      label: humanizeKey(key),
      value,
    })),
  ]

  return (
    <section className="card">
      <header className="card__header row-actions">
        <h2 className="card__title">Enriched profile</h2>
        {onEdit ? (
          <Button type="button" variant="ghost" onClick={onEdit}>
            Edit
          </Button>
        ) : null}
      </header>
      <div className="card__body">
      <p className="muted">
        {profile == null
          ? 'No enrichment saved yet — use Edit to add firmographics manually or wait for the enricher.'
          : 'Firmographics from CompanyProfile. Use Edit to update operator-entered enrichment.'}
      </p>
      <dl className="field-value-display__grid">
        {rows.map(({ key, label, value }) => (
          <div key={key} className="field-value-display">
            <dt>{label}</dt>
            <dd>
              <ProfileValue fieldKey={key} value={value} />
            </dd>
          </div>
        ))}
      </dl>
      </div>
    </section>
  )
}
