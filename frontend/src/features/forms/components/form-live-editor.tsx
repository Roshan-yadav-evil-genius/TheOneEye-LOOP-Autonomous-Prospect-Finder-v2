import { useMemo, useState, useEffect } from 'react'
import { Button } from '../../../shared/components/button'
import type { FormSectionDefinition } from '../form-field-schema'
import type { FormTheme } from '../form-themes'
import { FieldEditor } from './field-editor'

export interface FormLiveEditorProps {
  title: string
  sections: FormSectionDefinition[]
  themes?: FormTheme[]
  initialValue: Record<string, unknown>
  submitting?: boolean
  serverError?: string | null
  saved?: boolean
  onSubmit: (value: Record<string, unknown>) => Promise<void>
}

export function FormLiveEditor({
  title,
  sections,
  themes,
  initialValue,
  submitting = false,
  serverError,
  saved = false,
  onSubmit,
}: FormLiveEditorProps) {
  const [themeKey, setThemeKey] = useState(themes?.[0]?.key ?? '')
  const [sectionKey, setSectionKey] = useState(sections[0]?.key ?? '')
  const [form, setForm] = useState(initialValue)
  const [localError, setLocalError] = useState<string | null>(null)
  const [isDirty, setIsDirty] = useState(false)

  // Sync external initialValue when updated from backend / agent
  useEffect(() => {
    setForm(initialValue)
    setIsDirty(false)
  }, [initialValue])

  useEffect(() => {
    if (themes && themes.length > 0 && !themes.some((t) => t.key === themeKey)) {
      setThemeKey(themes[0].key)
    }
  }, [themes, themeKey])

  useEffect(() => {
    if (sections.length > 0 && !sections.some((s) => s.key === sectionKey)) {
      setSectionKey(sections[0].key)
    }
  }, [sections, sectionKey])

  const useThemes = Boolean(themes && themes.length > 0)
  const activeTheme = useMemo(
    () => themes?.find((theme) => theme.key === themeKey) ?? themes?.[0],
    [themeKey, themes],
  )
  
  const visibleSections = useMemo(() => {
    if (!useThemes || !activeTheme) return sections
    const keys = new Set(activeTheme.sectionKeys)
    return sections.filter((section) => keys.has(section.key))
  }, [activeTheme, sections, useThemes])

  useEffect(() => {
    if (visibleSections.length > 0 && !visibleSections.some((s) => s.key === sectionKey)) {
      setSectionKey(visibleSections[0].key)
    }
  }, [visibleSections, sectionKey])

  const currentSection = visibleSections.find((s) => s.key === sectionKey) ?? visibleSections[0]
  const currentSectionValue = form[currentSection?.key ?? '']

  const updateSection = (key: string, next: unknown) => {
    setForm((current) => ({ ...current, [key]: next }))
    setIsDirty(true)
  }

  const validateRequired = () => {
    for (const section of visibleSections) {
      const sectionValue = form[section.key]
      for (const field of section.fields) {
        if (!field.required) continue
        const value =
          field.path === '.'
            ? sectionValue
            : field.path
                .split('.')
                .reduce<unknown>(
                  (current, part) =>
                    current && typeof current === 'object'
                      ? (current as Record<string, unknown>)[part]
                      : undefined,
                  sectionValue,
                )
        if (value == null || value === '' || (Array.isArray(value) && value.length === 0)) {
          return `${section.title} -> ${field.label} is required.`
        }
      }
    }
    return null
  }

  const handleSave = async () => {
    const error = validateRequired()
    if (error) {
      setLocalError(error)
      return
    }
    setLocalError(null)
    await onSubmit(form)
    setIsDirty(false)
  }

  return (
    <div className="form-live-editor" style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', flex: 1, minHeight: 0, gap: '16px' }}>
      {/* Editor Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border-default)', paddingBottom: '14px', flexShrink: 0 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>{title}</h2>
          <span className="muted" style={{ fontSize: '0.825rem', marginTop: '2px', display: 'inline-block' }}>
            {isDirty ? '● Unsaved changes' : saved ? '✓ Saved' : 'Live Form Editor'}
          </span>
        </div>
        <Button type="button" onClick={() => void handleSave()} disabled={submitting}>
          {submitting ? 'Saving…' : 'Save Changes'}
        </Button>
      </div>

      {/* Theme Tabs Pill Navigation */}
      {useThemes ? (
        <nav className="wizard-themes" aria-label="Form themes" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', flexShrink: 0 }}>
          {themes!.map((theme) => (
            <button
              type="button"
              key={theme.key}
              className={activeTheme?.key === theme.key ? 'active' : ''}
              onClick={() => setThemeKey(theme.key)}
            >
              {theme.label}
            </button>
          ))}
        </nav>
      ) : null}

      {/* Main Form Body Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '20px', flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* Left Sub-Navigation */}
        <nav 
          aria-label="Form sections" 
          style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '4px', 
            borderRight: '1px solid var(--color-border-default)', 
            paddingRight: '14px',
            overflowY: 'auto' 
          }}
        >
          {visibleSections.map((item) => (
            <button
              type="button"
              key={item.key}
              className={`entity-edit-dialog__nav-item ${sectionKey === item.key ? 'active' : ''}`}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderRadius: 'var(--radius-md)',
                background: sectionKey === item.key ? 'var(--color-bg-elevated)' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: sectionKey === item.key ? 700 : 'normal',
                color: sectionKey === item.key ? 'var(--color-accent-primary)' : 'var(--color-text-primary)',
                transition: 'all 0.15s ease'
              }}
              onClick={() => setSectionKey(item.key)}
            >
              {item.title}
            </button>
          ))}
        </nav>

        {/* Right Section Content (Scrollable) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '6px' }}>
          {currentSection ? (
            <>
              <div>
                <h3 className="section-heading" style={{ marginTop: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                  {currentSection.title}
                </h3>
                <p className="muted" style={{ margin: '4px 0 16px 0', fontSize: '0.85rem' }}>
                  {currentSection.help}
                </p>
              </div>
              <div className="field-grid" style={{ display: 'grid', gap: '16px' }}>
                {currentSection.fields.map((field) => (
                  <FieldEditor
                    key={`${currentSection.key}.${field.path}.${field.label}`}
                    field={field}
                    sectionValue={currentSectionValue}
                    onChange={(next) => updateSection(currentSection.key, next)}
                  />
                ))}
              </div>
            </>
          ) : null}

          {localError ? <p role="alert" className="error-banner">{localError}</p> : null}
          {serverError ? <p role="alert" className="error-banner">{serverError}</p> : null}
        </div>
      </div>
    </div>
  )
}
