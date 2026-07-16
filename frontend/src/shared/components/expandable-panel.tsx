import type { PropsWithChildren, ReactNode } from 'react'
import { useId, useState } from 'react'

export function ExpandablePanel({
  title,
  children,
  defaultOpen = false,
  summary,
}: PropsWithChildren<{
  title: string
  defaultOpen?: boolean
  summary?: ReactNode
}>) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = useId()

  return (
    <section className="expandable-panel">
      <button
        type="button"
        className="expandable-panel__toggle"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{title}</span>
        {summary ? <span className="expandable-panel__summary">{summary}</span> : null}
        <span className="expandable-panel__chevron" aria-hidden>
          {open ? '▾' : '▸'}
        </span>
      </button>
      {open ? (
        <div id={panelId} className="expandable-panel__body">
          {children}
        </div>
      ) : null}
    </section>
  )
}
