import type { HTMLAttributes, PropsWithChildren, ReactNode } from 'react'
import { clsx } from 'clsx'

import { Button } from './button'
import { Card } from './card'

export function Badge({
  children,
  tone = 'info',
}: PropsWithChildren<{ tone?: 'info' | 'success' | 'danger' | 'warning' }>) {
  return <span className={clsx('badge', `badge--${tone}`)}>{children}</span>
}

export function SearchField({
  value,
  onChange,
  placeholder,
  label,
}: {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label?: string
}) {
  return (
    <label className="search-field-wrap">
      {label ? <span className="visually-hidden">{label}</span> : null}
      <input
        className="search-field"
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label ?? placeholder ?? 'Search'}
      />
    </label>
  )
}

export function DataTable({
  headers,
  children,
  empty,
}: {
  headers: string[]
  children?: ReactNode
  empty?: ReactNode
}) {
  const rows = Array.isArray(children)
    ? children.filter(Boolean)
    : children
      ? [children]
      : []
  const hasRows = rows.length > 0

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {hasRows ? (
            rows
          ) : (
            <tr>
              <td colSpan={headers.length}>
                {empty ?? <p className="muted">No rows.</p>}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export function SideRail({
  title,
  children,
}: PropsWithChildren<{ title: string }>) {
  return (
    <aside className="side-rail">
      <h2>{title}</h2>
      {children}
    </aside>
  )
}

export function WhiteboardPanel({
  content,
  onChange,
  onSave,
}: {
  content: string
  onChange: (value: string) => void
  onSave: () => void
}) {
  return (
    <Card title="Whiteboard">
      <textarea rows={16} value={content} onChange={(event) => onChange(event.target.value)} />
      <Button onClick={onSave}>Save</Button>
    </Card>
  )
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string
  body: string
  action?: ReactNode
}) {
  return (
    <Card title={title}>
      <p className="muted">{body}</p>
      {action}
    </Card>
  )
}

export function ProcessControls(props: HTMLAttributes<HTMLDivElement>) {
  return <div className="process-controls" {...props} />
}

export function FilterChips({
  options,
  value,
  onChange,
  label,
}: {
  options: Array<{ value: string; label: string }>
  value: string
  onChange: (value: string) => void
  label: string
}) {
  return (
    <div className="filter-chips" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={clsx('filter-chip', value === option.value && 'active')}
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
