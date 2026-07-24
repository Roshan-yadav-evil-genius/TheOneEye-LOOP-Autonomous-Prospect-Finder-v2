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

function isImageUrl(url: string): boolean {
  if (!url) return false
  const lower = url.toLowerCase()
  return (
    lower.startsWith('/static/') ||
    /\.(png|jpg|jpeg|gif|svg|webp)($|\?)/i.test(lower) ||
    lower.includes('/uploads/')
  )
}

function isWebUrl(url: string): boolean {
  if (!url) return false
  return url.startsWith('http://') || url.startsWith('https://')
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

  const isImageField =
    field.kind === 'file' ||
    field.path.includes('thumbnail_url') ||
    field.path.includes('logo') ||
    (typeof value === 'string' && isImageUrl(value))

  if (field.kind === 'boolean') {
    content = value == null ? '—' : value ? 'Yes' : 'No'
  } else if (isImageField) {
    if (!isEmpty(value) && typeof value === 'string') {
      content = (
        <div className="field-value-display__image-preview">
          <img
            src={value}
            alt={field.label}
            className="field-value-display__img"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="field-value-display__link"
          >
            View image ↗
          </a>
        </div>
      )
    } else {
      content = <span className="muted">—</span>
    }
  } else if (field.kind === 'string-list' || field.kind === 'multi-select') {
    const list = Array.isArray(value) ? (value as unknown[]).map(formatScalar).filter(Boolean) : []
    content =
      list.length === 0 ? (
        '—'
      ) : (
        <div className="field-value-display__chips">
          {list.map((item) => (
            <span key={item} className="field-value-display__chip">
              {item}
            </span>
          ))}
        </div>
      )
  } else if (field.kind === 'object-list') {
    const rows = Array.isArray(value) ? (value as Record<string, unknown>[]) : []
    content =
      rows.length === 0 ? (
        '—'
      ) : (
        <div className="field-value-display__object-cards">
          {rows.map((row, index) => {
            const itemTitle = (row.title || row.name || row.hypothesis || `Item #${index + 1}`) as string
            return (
              <div key={`${field.path}-${index}`} className="field-value-display__object-card">
                <div className="field-value-display__object-card-header">
                  <span className="field-value-display__object-card-badge">#{index + 1}</span>
                  <h4 className="field-value-display__object-card-title">{itemTitle}</h4>
                </div>
                <dl className="field-value-display__grid">
                  {(field.itemFields ?? []).map((item) => (
                    <FieldValueDisplay key={item.path} field={item} sectionValue={row} />
                  ))}
                </dl>
              </div>
            )
          })}
        </div>
      )
  } else if (!isEmpty(value)) {
    const formatted = formatScalar(value)
    if (typeof value === 'string' && isWebUrl(formatted)) {
      content = (
        <a
          href={formatted}
          target="_blank"
          rel="noopener noreferrer"
          className="field-value-display__link"
        >
          {formatted} ↗
        </a>
      )
    } else {
      content = formatted
    }
  }

  const isFullWidth = field.kind === 'object-list' || field.kind === 'textarea'

  return (
    <div className={`field-value-display ${isFullWidth ? 'field-value-display--full' : ''}`.trim()}>
      <dt>
        <span className="field-value-display__label">{field.label}</span>
        {field.help ? <span className="field-value-display__help muted">{field.help}</span> : null}
      </dt>
      <dd>{content}</dd>
    </div>
  )
}

