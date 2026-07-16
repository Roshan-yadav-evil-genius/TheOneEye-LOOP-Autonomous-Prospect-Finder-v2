import type { ReactNode } from 'react'

export function KpiStrip({
  items,
  label = 'Key metrics',
}: {
  items: Array<{ label: string; value: ReactNode }>
  label?: string
}) {
  return (
    <dl className="kpi-strip" aria-label={label}>
      {items.map((item) => (
        <div key={item.label} className="kpi-strip__item">
          <dt className="kpi-strip__label">{item.label}</dt>
          <dd className="kpi-strip__value">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}
