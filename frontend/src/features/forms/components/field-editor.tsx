import { FormField, FormFieldset } from '../../../shared/components/form-field'
import type { FormField as FormFieldDef } from '../form-field-schema'
import { getAtPath, parseList, setAtPath } from '../path-utils'

interface FieldEditorProps {
  field: FormFieldDef
  sectionValue: unknown
  readOnly?: boolean
  onChange: (nextSectionValue: unknown) => void
}

export function FieldEditor({
  field,
  onChange,
  readOnly = false,
  sectionValue,
}: FieldEditorProps) {
  const value = getAtPath(sectionValue, field.path)

  const update = (next: unknown) => {
    if (readOnly) return
    onChange(setAtPath(sectionValue, field.path, next))
  }

  if (field.kind === 'textarea') {
    return (
      <FormField label={field.label} required={field.required} help={field.help}>
        <textarea
          className="control"
          rows={4}
          readOnly={readOnly}
          disabled={readOnly}
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => update(event.target.value)}
        />
      </FormField>
    )
  }

  if (field.kind === 'number') {
    return (
      <FormField label={field.label} required={field.required} help={field.help}>
        <input
          className="control"
          type="number"
          readOnly={readOnly}
          disabled={readOnly}
          value={value == null ? '' : String(value)}
          onChange={(event) =>
            update(event.target.value === '' ? null : Number(event.target.value))
          }
        />
      </FormField>
    )
  }

  if (field.kind === 'boolean') {
    return (
      <FormField label={field.label} help={field.help}>
        <input
          type="checkbox"
          disabled={readOnly}
          checked={Boolean(value)}
          onChange={(event) => update(event.target.checked)}
        />
      </FormField>
    )
  }

  if (field.kind === 'select') {
    return (
      <FormField label={field.label} required={field.required} help={field.help}>
        <select
          className="control"
          disabled={readOnly}
          value={typeof value === 'string' ? value : (field.options?.[0] ?? '')}
          onChange={(event) => update(event.target.value)}
        >
          {(field.options ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </FormField>
    )
  }

  if (field.kind === 'multi-select') {
    const selected = Array.isArray(value) ? (value as string[]) : []
    return (
      <FormFieldset label={field.label} required={field.required} help={field.help} disabled={readOnly}>
        <div className="checkbox-grid">
          {(field.options ?? []).map((option) => {
            const checked = selected.includes(option)
            return (
              <FormField key={option} label={option} inline>
                <input
                  type="checkbox"
                  disabled={readOnly}
                  checked={checked}
                  onChange={(event) => {
                    if (event.target.checked) update([...selected, option])
                    else update(selected.filter((item) => item !== option))
                  }}
                />
              </FormField>
            )
          })}
        </div>
      </FormFieldset>
    )
  }

  if (field.kind === 'string-list') {
    const list = Array.isArray(value) ? (value as string[]) : []
    return (
      <FormField label={field.label} required={field.required} help={field.help}>
        <textarea
          className="control"
          rows={4}
          readOnly={readOnly}
          disabled={readOnly}
          placeholder="One item per line"
          value={list.join('\n')}
          onChange={(event) => update(parseList(event.target.value))}
        />
      </FormField>
    )
  }

  if (field.kind === 'object-list') {
    const rows = Array.isArray(value) ? (value as Record<string, unknown>[]) : []
    return (
      <div className="field field--group">
        <span className="field__label">{field.label}</span>
        {field.help ? <span className="field__help">{field.help}</span> : null}
        {rows.map((row, index) => (
          <div className="object-row" key={`${field.path}-${index}`}>
            {(field.itemFields ?? []).map((item) => (
              <FieldEditor
                key={item.path}
                field={item}
                sectionValue={row}
                readOnly={readOnly}
                onChange={(nextRow) => {
                  const next = [...rows]
                  next[index] = nextRow as Record<string, unknown>
                  update(next)
                }}
              />
            ))}
            {readOnly ? null : (
              <button
                type="button"
                className="button button--danger"
                onClick={() => update(rows.filter((_, i) => i !== index))}
              >
                Remove
              </button>
            )}
          </div>
        ))}
        {readOnly ? null : (
          <button
            type="button"
            className="button button--ghost"
            onClick={() =>
              update([
                ...rows,
                Object.fromEntries((field.itemFields ?? []).map((item) => [item.path, ''])),
              ])
            }
          >
            Add row
          </button>
        )}
      </div>
    )
  }

  return (
    <FormField label={field.label} required={field.required} help={field.help}>
      <input
        className="control"
        type="text"
        readOnly={readOnly}
        disabled={readOnly}
        value={typeof value === 'string' || typeof value === 'number' ? String(value) : ''}
        onChange={(event) => update(event.target.value)}
      />
    </FormField>
  )
}
