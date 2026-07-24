import type { ReactNode } from 'react'

import { Badge } from '../../../shared/components/design-system'
import { Card } from '../../../shared/components/card'
import { EditIcon, IconLink } from '../../../shared/components/icon-button'
import type { FormSectionDefinition } from '../form-field-schema'
import type { FormTheme } from '../form-themes'
import { FieldValueDisplay } from './field-value-display'

export function FormProfileViewer({
  title,
  validated,
  sections,
  value,
  themes,
  actions,
  hint = 'Read-only profile — click edit to modify values.',
  getEditUrl,
}: {
  title: string
  validated: boolean
  sections: FormSectionDefinition[]
  value: Record<string, unknown>
  /** Optional theme headings that group section cards. */
  themes?: FormTheme[]
  actions?: ReactNode
  hint?: string
  getEditUrl?: (sectionKey: string) => string
}) {
  const groups =
    themes && themes.length > 0
      ? themes.map((theme) => ({
          key: theme.key,
          label: theme.label,
          sections: sections.filter((section) => theme.sectionKeys.includes(section.key)),
        }))
      : [{ key: 'all', label: null as string | null, sections }]

  return (
    <div className="form-profile-viewer">
      <Card title={title}>
        <div className="profile-summary__status">
          <Badge tone={validated ? 'success' : 'warning'}>
            {validated ? 'Validated' : 'Incomplete'}
          </Badge>
          {actions}
        </div>
        <p className="muted">{hint}</p>
      </Card>

      {groups.map((group) => (
        <div key={group.key} className="form-profile-viewer__group">
          {group.label ? (
            <h3 className="form-profile-viewer__group-title">{group.label}</h3>
          ) : null}
          <div className="form-profile-viewer__sections">
            {group.sections.map((section) => {
              const editUrl = getEditUrl?.(section.key)
              return (
                <Card
                  key={section.key}
                  title={
                    <div className="form-profile-viewer__section-header">
                      <span>{section.title}</span>
                      {editUrl ? (
                        <IconLink to={editUrl} label={`Edit ${section.title}`}>
                          <EditIcon />
                        </IconLink>
                      ) : null}
                    </div>
                  }
                >
                  {section.help ? <p className="muted">{section.help}</p> : null}
                  <dl className="field-value-display__grid">
                    {section.fields.map((field) => (
                      <FieldValueDisplay
                        key={`${section.key}.${field.path}.${field.label}`}
                        field={field}
                        sectionValue={value[section.key]}
                      />
                    ))}
                  </dl>
                </Card>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

