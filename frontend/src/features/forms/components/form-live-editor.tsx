import { useMemo, useState, useEffect } from 'react'
import { Button } from '../../../shared/components/button'
import type { FormSectionDefinition } from '../form-field-schema'
import type { FormTheme } from '../form-themes'
import { FieldEditor } from './field-editor'
import { formsApi, type FormTemplateKey } from '../api/forms-api'
import { downloadTextFile } from '../lib/download-markdown'
import { exportFilledMarkdown } from '../lib/export-filled-markdown'

export interface FormLiveEditorProps {
  title: string
  sections: FormSectionDefinition[]
  themes?: FormTheme[]
  initialValue: Record<string, unknown>
  initialSectionKey?: string
  initialThemeKey?: string
  submitting?: boolean
  serverError?: string | null
  saved?: boolean
  onSubmit: (value: Record<string, unknown>) => Promise<void>
  formKey?: FormTemplateKey
}

export function FormLiveEditor({
  title,
  sections,
  themes,
  initialValue,
  initialSectionKey,
  initialThemeKey,
  submitting = false,
  serverError,
  saved = false,
  onSubmit,
  formKey,
}: FormLiveEditorProps) {
  const defaultThemeKey = useMemo(() => {
    if (initialThemeKey) return initialThemeKey
    if (initialSectionKey && themes) {
      const match = themes.find((t) => t.sectionKeys.includes(initialSectionKey))
      if (match) return match.key
    }
    return themes?.[0]?.key ?? ''
  }, [initialSectionKey, initialThemeKey, themes])

  const defaultSectionKey = useMemo(() => {
    if (initialSectionKey && sections.some((s) => s.key === initialSectionKey)) {
      return initialSectionKey
    }
    return sections[0]?.key ?? ''
  }, [initialSectionKey, sections])

  const [themeKey, setThemeKey] = useState(defaultThemeKey)
  const [sectionKey, setSectionKey] = useState(defaultSectionKey)
  const [form, setForm] = useState(initialValue)
  const [localError, setLocalError] = useState<string | null>(null)
  const [isDirty, setIsDirty] = useState(false)

  const resolvedFormKey = useMemo<FormTemplateKey | undefined>(() => {
    if (formKey) return formKey
    const lower = title.toLowerCase()
    if (lower.includes('org')) return 'organization'
    if (lower.includes('product')) return 'product'
    if (lower.includes('strateg')) return 'sales-strategy'
    return undefined
  }, [formKey, title])

  const [downloadingTemplate, setDownloadingTemplate] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const handleDownloadTemplate = async () => {
    if (!resolvedFormKey) return
    setDownloadingTemplate(true)
    setDownloadError(null)
    try {
      const template = await formsApi.downloadTemplate(resolvedFormKey)
      downloadTextFile(template.filename, template.content)
    } catch {
      setDownloadError('Could not download the offline form template.')
    } finally {
      setDownloadingTemplate(false)
    }
  }

  const handleExportFilled = () => {
    exportFilledMarkdown(title, sections, form)
  }

  // Update selection if initialSectionKey/initialThemeKey change externally
  useEffect(() => {
    if (initialSectionKey && sections.some((s) => s.key === initialSectionKey)) {
      setSectionKey(initialSectionKey)
      if (themes) {
        const match = themes.find((t) => t.sectionKeys.includes(initialSectionKey))
        if (match) setThemeKey(match.key)
      }
    } else if (initialThemeKey && themes?.some((t) => t.key === initialThemeKey)) {
      setThemeKey(initialThemeKey)
    }
  }, [initialSectionKey, initialThemeKey, sections, themes])

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
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {resolvedFormKey ? (
            <Button
              variant="ghost"
              type="button"
              disabled={downloadingTemplate}
              onClick={() => void handleDownloadTemplate()}
            >
              {downloadingTemplate ? 'Downloading…' : 'Download Template'}
            </Button>
          ) : null}
          <Button variant="secondary" type="button" onClick={handleExportFilled}>
            Export Filled Markdown
          </Button>
          <Button type="button" onClick={() => void handleSave()} disabled={submitting}>
            {submitting ? 'Saving…' : 'Save Changes'}
          </Button>
        </div>
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

          {downloadError ? <p role="alert" className="error-banner">{downloadError}</p> : null}
          {localError ? <p role="alert" className="error-banner">{localError}</p> : null}
          {serverError ? <p role="alert" className="error-banner">{serverError}</p> : null}
        </div>
      </div>
    </div>
  )
}
