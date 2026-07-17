import * as Dialog from '@radix-ui/react-dialog'
import { useMemo, useState, useEffect } from 'react'

import { Button } from '../../../shared/components/button'
import type { FormSectionDefinition } from '../form-field-schema'
import type { FormTheme } from '../form-themes'
import { FieldEditor } from './field-editor'

interface EntityEditModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  sections: FormSectionDefinition[]
  themes?: FormTheme[]
  initialValue: Record<string, unknown>
  submitting?: boolean
  serverError?: string | null
  onSubmit: (value: Record<string, unknown>) => Promise<void>
}

export function EntityEditModal({
  open,
  onOpenChange,
  title,
  sections,
  themes,
  initialValue,
  submitting,
  serverError,
  onSubmit,
}: EntityEditModalProps) {
  const [themeKey, setThemeKey] = useState(themes?.[0]?.key ?? '')
  const [sectionKey, setSectionKey] = useState(sections[0]?.key ?? '')
  const [form, setForm] = useState(initialValue)
  const [localError, setLocalError] = useState<string | null>(null)

  // Reset state when modal opens
  useEffect(() => {
    if (open) {
      setForm(initialValue)
      setLocalError(null)
      if (themes && themes.length > 0) {
        setThemeKey(themes[0].key)
      }
      if (sections.length > 0) {
        setSectionKey(sections[0].key)
      }
    }
  }, [open, initialValue, themes, sections])

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

  // Ensure selected section is always visible
  useEffect(() => {
    if (visibleSections.length > 0 && !visibleSections.find(s => s.key === sectionKey)) {
      setSectionKey(visibleSections[0].key)
    }
  }, [visibleSections, sectionKey])

  const currentSection = visibleSections.find((s) => s.key === sectionKey) ?? visibleSections[0]
  const currentSectionValue = form[currentSection?.key ?? '']

  const updateSection = (key: string, next: unknown) => {
    setForm((current) => ({ ...current, [key]: next }))
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

  const submitAll = async () => {
    const error = validateRequired()
    if (error) {
      setLocalError(error)
      return
    }
    setLocalError(null)
    await onSubmit(form)
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="entity-edit-dialog">
          <div className="entity-edit-dialog__layout">
            <div className="entity-edit-dialog__sidebar">
              <div className="dialog-header entity-edit-dialog__header">
                <Dialog.Title className="dialog-title">Edit {title}</Dialog.Title>
                <Dialog.Description className="visually-hidden">Edit details for {title}</Dialog.Description>
              </div>
              
              {useThemes ? (
                <nav className="wizard-themes" aria-label={`Themes`} style={{ marginBottom: '1rem' }}>
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

              <nav className="entity-edit-dialog__nav" aria-label={`Sections`}>
                {visibleSections.map((item) => (
                  <button
                    type="button"
                    key={item.key}
                    className={`entity-edit-dialog__nav-item ${sectionKey === item.key ? 'active' : ''}`}
                    onClick={() => setSectionKey(item.key)}
                  >
                    {item.title}
                  </button>
                ))}
              </nav>
            </div>

            <div className="entity-edit-dialog__main">
              <div className="entity-edit-dialog__content">
                {currentSection ? (
                  <>
                    <h3 className="section-heading" style={{ marginTop: 0 }}>{currentSection.title}</h3>
                    <p className="muted">{currentSection.help}</p>
                    <div className="field-grid">
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

              <div className="dialog-footer entity-edit-dialog__footer">
                <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button type="button" disabled={submitting} onClick={() => void submitAll()}>
                  {submitting ? 'Saving…' : 'Save'}
                </Button>
              </div>
              <Dialog.Close asChild>
                <button type="button" className="dialog-close" aria-label="Close" style={{ top: '1rem', right: '1rem' }}>
                  ×
                </button>
              </Dialog.Close>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
