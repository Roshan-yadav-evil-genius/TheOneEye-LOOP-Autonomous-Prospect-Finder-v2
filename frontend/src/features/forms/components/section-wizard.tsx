import { useMemo, useState } from 'react'

import { Button } from '../../../shared/components/button'
import { Card } from '../../../shared/components/card'
import type { FormSectionDefinition } from '../form-field-schema'
import type { FormTheme } from '../form-themes'
import { FieldEditor } from './field-editor'

interface WizardProps {
  title: string
  sections: FormSectionDefinition[]
  initialValue: Record<string, unknown>
  submitting?: boolean
  serverError?: string | null
  readOnly?: boolean
  readOnlyHint?: string
  submitLabel?: string
  /** When set, sections are navigated via theme groups (edit mode). */
  themes?: FormTheme[]
  onSubmit?: (value: Record<string, unknown>) => Promise<void>
  onIncrementalSave?: (value: Record<string, unknown>) => Promise<void>
}

export function SectionWizard({
  initialValue,
  onSubmit,
  readOnly = false,
  readOnlyHint = 'Read-only snapshot — values cannot be edited after creation.',
  sections,
  serverError,
  submitLabel,
  submitting,
  themes,
  title,
  onIncrementalSave,
}: WizardProps) {
  const [step, setStep] = useState(0)
  const [themeKey, setThemeKey] = useState(themes?.[0]?.key ?? '')
  const [form, setForm] = useState(initialValue)
  const [localError, setLocalError] = useState<string | null>(null)

  const useThemes = Boolean(themes && themes.length > 0 && !readOnly)
  const activeTheme = useMemo(
    () => themes?.find((theme) => theme.key === themeKey) ?? themes?.[0],
    [themeKey, themes],
  )
  const visibleSections = useMemo(() => {
    if (!useThemes || !activeTheme) return sections
    const keys = new Set(activeTheme.sectionKeys)
    return sections.filter((section) => keys.has(section.key))
  }, [activeTheme, sections, useThemes])

  const section = useThemes ? visibleSections[Math.min(step, visibleSections.length - 1)] : sections[step]
  const sectionValue = form[section.key]
  const sectionIndexInAll = sections.findIndex((item) => item.key === section.key)

  const updateSection = (next: unknown) => {
    if (readOnly) return
    setForm((current) => ({ ...current, [section.key]: next }))
  }

  const validateRequired = () => {
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
        return `${field.label} is required.`
      }
    }
    return null
  }

  const goToStep = (index: number) => {
    setLocalError(null)
    setStep(index)
  }

  const selectTheme = (key: string) => {
    setThemeKey(key)
    setStep(0)
    setLocalError(null)
  }

  const [savingIncremental, setSavingIncremental] = useState(false)

  const continueNext = async () => {
    if (!readOnly) {
      const error = validateRequired()
      if (error) {
        setLocalError(error)
        return
      }
    }
    setLocalError(null)
    
    if (onIncrementalSave && !readOnly) {
      try {
        setSavingIncremental(true)
        await onIncrementalSave(form)
      } catch (err) {
        // Handle error if needed, for now just let it fall through or show local error
        setLocalError('Failed to save progress. Please try again.')
        return
      } finally {
        setSavingIncremental(false)
      }
    }

    const max = (useThemes ? visibleSections : sections).length - 1
    if (step < max) {
      setStep((current) => current + 1)
      return
    }
    if (useThemes && themes) {
      const themeIndex = themes.findIndex((theme) => theme.key === activeTheme?.key)
      if (themeIndex >= 0 && themeIndex < themes.length - 1) {
        selectTheme(themes[themeIndex + 1].key)
      }
    }
  }

  const goPrevious = () => {
    if (step > 0) {
      setStep(step - 1)
      return
    }
    if (useThemes && themes && activeTheme) {
      const themeIndex = themes.findIndex((theme) => theme.key === activeTheme.key)
      if (themeIndex > 0) {
        const prev = themes[themeIndex - 1]
        setThemeKey(prev.key)
        const prevSections = sections.filter((s) => prev.sectionKeys.includes(s.key))
        setStep(Math.max(0, prevSections.length - 1))
      }
    }
  }

  const isLastSection = useThemes
    ? Boolean(
        activeTheme &&
          themes &&
          themes[themes.length - 1]?.key === activeTheme.key &&
          step >= visibleSections.length - 1,
      )
    : step >= sections.length - 1

  const canGoPrevious = useThemes
    ? step > 0 || (themes?.findIndex((t) => t.key === activeTheme?.key) ?? 0) > 0
    : step > 0

  const submitAll = async () => {
    if (readOnly || !onSubmit) return
    const error = validateRequired()
    if (error) {
      setLocalError(error)
      return
    }
    setLocalError(null)
    await onSubmit(form)
  }

  const navSections = useThemes ? visibleSections : sections

  return (
    <div className={`wizard-layout${readOnly ? ' wizard-layout--readonly' : ''}`}>
      <div className="wizard-nav">
        {useThemes ? (
          <nav className="wizard-themes" aria-label={`${title} themes`}>
            {themes!.map((theme) => (
              <button
                type="button"
                key={theme.key}
                className={activeTheme?.key === theme.key ? 'active' : ''}
                onClick={() => selectTheme(theme.key)}
              >
                {theme.label}
              </button>
            ))}
          </nav>
        ) : null}
        <nav className="wizard-steps" aria-label={`${title} sections`}>
          {navSections.map((item, index) => {
            const globalIndex = sections.findIndex((s) => s.key === item.key)
            return (
              <button
                type="button"
                key={item.key}
                className={step === index ? 'active' : ''}
                onClick={() => goToStep(index)}
              >
                <span>{globalIndex + 1}</span>
                {item.title}
              </button>
            )
          })}
        </nav>
      </div>
      <Card title={`${sectionIndexInAll + 1}. ${section.title}`}>
        <p className="muted">{section.help}</p>
        {readOnly ? <p className="muted">{readOnlyHint}</p> : null}
        <div className="field-grid">
          {section.fields.map((field) => (
            <FieldEditor
              key={`${section.key}.${field.path}.${field.label}`}
              field={field}
              sectionValue={sectionValue}
              readOnly={readOnly}
              onChange={updateSection}
            />
          ))}
        </div>
        {localError ? <p role="alert" className="error-banner">{localError}</p> : null}
        {serverError ? <p role="alert" className="error-banner">{serverError}</p> : null}
        <div className="row-actions">
          <Button type="button" variant="ghost" disabled={!canGoPrevious || savingIncremental} onClick={goPrevious}>
            Previous
          </Button>
          {!isLastSection ? (
            <Button type="button" disabled={savingIncremental} onClick={() => void continueNext()}>
              {savingIncremental ? 'Saving…' : (readOnly ? 'Next' : (onIncrementalSave ? 'Save & Continue' : 'Continue'))}
            </Button>
          ) : readOnly ? null : (
            <Button type="button" disabled={submitting} onClick={() => void submitAll()}>
              {submitting ? 'Saving…' : (submitLabel ?? `Submit ${title}`)}
            </Button>
          )}
        </div>
      </Card>
    </div>
  )
}
