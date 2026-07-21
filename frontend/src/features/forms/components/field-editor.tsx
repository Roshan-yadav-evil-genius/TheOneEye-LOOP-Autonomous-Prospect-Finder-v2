import { useRef, useState, useEffect } from 'react'
import { FormField, FormFieldset } from '../../../shared/components/form-field'
import type { FormField as FormFieldDef } from '../form-field-schema'
import { getAtPath, parseList, setAtPath } from '../path-utils'
import { Button } from '../../../shared/components/button'
import { useUploadUrl } from '../contexts/upload-context'

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

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [localFile, setLocalFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const uploadUrl = useUploadUrl()

  useEffect(() => {
    if (!localFile) {
      setPreviewUrl('')
      return
    }
    const url = URL.createObjectURL(localFile)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [localFile])

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

  if (field.kind === 'file') {
    if (!uploadUrl) return null

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0]
      if (!file) return
      
      setLocalFile(file)
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${uploadUrl}`, {
          method: 'POST',
          body: formData,
        })
        const data = await response.json()
        if (data.url) {
          update(data.url)
        }
      } catch (e) {
        console.error('Upload failed', e)
        setLocalFile(null)
      }
    }

    const hasValue = typeof value === 'string' && value !== ''
    const displayUrl = previewUrl || (hasValue ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${value}` : '')

    return (
      <FormField label={field.label} required={field.required} help={field.help}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {displayUrl ? (
            <div style={{ position: 'relative', width: 64, height: 64, border: '1px solid var(--border-color, #ccc)', borderRadius: '8px', overflow: 'hidden', backgroundColor: 'var(--bg-muted, #f3f4f6)' }}>
              <img
                src={displayUrl}
                alt="Preview"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              {!readOnly && (
                <button
                  type="button"
                  onClick={() => {
                    setLocalFile(null)
                    setPreviewUrl('')
                    update('')
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                  style={{
                    position: 'absolute',
                    top: 4,
                    right: 4,
                    background: 'rgba(0,0,0,0.6)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: 20,
                    height: 20,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    padding: 0
                  }}
                  title="Remove file"
                >
                  ✕
                </button>
              )}
            </div>
          ) : null}

          {!readOnly && (
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => void handleFileChange(e)}
                style={{ display: 'none' }}
              />
              <Button 
                type="button" 
                variant="ghost" 
                onClick={() => fileInputRef.current?.click()}
              >
                Upload File
              </Button>
            </div>
          )}
        </div>
      </FormField>
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
