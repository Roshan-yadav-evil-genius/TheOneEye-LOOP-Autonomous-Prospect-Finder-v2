import type { PropsWithChildren, ReactNode } from 'react'
import { clsx } from 'clsx'

export function FormField({
  label,
  required = false,
  help,
  error,
  inline = false,
  className,
  children,
}: PropsWithChildren<{
  label: ReactNode
  required?: boolean
  help?: ReactNode
  error?: ReactNode
  inline?: boolean
  className?: string
}>) {
  const labelNode = (
    <span className="field__label">
      {label}
      {required ? <span className="field__required"> *</span> : null}
    </span>
  )

  return (
    <label className={clsx('field', inline && 'field--inline', className)}>
      {inline ? (
        <>
          {children}
          {labelNode}
        </>
      ) : (
        <>
          {labelNode}
          {help ? <span className="field__help">{help}</span> : null}
          {children}
        </>
      )}
      {error ? (
        <span className="field__error" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  )
}

export function FormFieldset({
  label,
  required = false,
  help,
  disabled = false,
  children,
}: PropsWithChildren<{
  label: ReactNode
  required?: boolean
  help?: ReactNode
  disabled?: boolean
}>) {
  return (
    <fieldset className="field field--group" disabled={disabled}>
      <legend className="field__label">
        {label}
        {required ? <span className="field__required"> *</span> : null}
      </legend>
      {help ? <span className="field__help">{help}</span> : null}
      {children}
    </fieldset>
  )
}
