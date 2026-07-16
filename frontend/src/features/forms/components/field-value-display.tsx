import type { ReactNode } from 'react'

import type { FormField } from '../form-field-schema'
import { getAtPath } from '../path-utils'

function isEmpty(value: unknown): boolean {
  if (value == null) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  return false
}

function formatScalar(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string') return value
  return String(value)
}

export function FieldValueDisplay({
  field,
  sectionValue,
}: {
  field: FormField
  sectionValue: unknown
}) {
  const value = getAtPath(sectionValue, field.path)

  let content: ReactNode = '—'

  if (field.kind === 'boolean') {
    content = value == null ? '—' : value ? 'Yes' : 'No'
  } else if (field.kind === 'string-list' || field.kind === 'multi-select') {
    const list = Array.isArray(value) ? (value as unknown[]).map(formatScalar).filter(Boolean) : []
    content =
      list.length === 0 ? (
        '—'
      ) : (
        <ul className="field-value-display__list">
          {list.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )
  } else if (field.kind === 'object-list') {
    const rows = Array.isArray(value) ? (value as Record<string, unknown>[]) : []
    content =
      rows.length === 0 ? (
        '—'
      ) : (
        <ul className="field-value-display__objects">
          {rows.map((row, index) => (
            <li key={`${field.path}-${index}`} className="field-value-display__object">
              <dl className="field-value-display__grid">
                {(field.itemFields ?? []).map((item) => (
                  <FieldValueDisplay key={item.path} field={item} sectionValue={row} />
                ))}
              </dl>
            </li>
          ))}
        </ul>
      )
  } else if (!isEmpty(value)) {
    content = formatScalar(value)
  }

  return (
    <div className="field-value-display">
      <dt>
        {field.label}
        {field.help ? <span className="field-value-display__help muted">{field.help}</span> : null}
      </dt>
      <dd>{content}</dd>
    </div>
  )
}
