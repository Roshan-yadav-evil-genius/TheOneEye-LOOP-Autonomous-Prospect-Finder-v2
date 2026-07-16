import type { ReactNode } from 'react'

import { Badge } from './design-system'
import { Card } from './card'

export interface ProfileSummaryField {
  label: string
  value: ReactNode
}

export function ProfileSummary({
  title,
  validated,
  fields,
  actions,
}: {
  title: string
  validated: boolean
  fields: ProfileSummaryField[]
  actions?: ReactNode
}) {
  return (
    <Card title={title}>
      <div className="profile-summary__status">
        <Badge tone={validated ? 'success' : 'warning'}>
          {validated ? 'Validated' : 'Incomplete'}
        </Badge>
        {actions}
      </div>
      <dl className="profile-summary__grid">
        {fields.map((field) => (
          <div key={field.label} className="profile-summary__field">
            <dt>{field.label}</dt>
            <dd>{field.value || '—'}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}
