import * as Dialog from '@radix-ui/react-dialog'
import type { PropsWithChildren, ReactNode } from 'react'

import { Button } from './button'

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  contentStyle,
}: PropsWithChildren<{
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  footer?: ReactNode
  contentStyle?: React.CSSProperties
}>) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content" style={contentStyle}>
          <div className="dialog-header">
            <Dialog.Title className="dialog-title">{title}</Dialog.Title>
            {description ? (
              <Dialog.Description className="dialog-description">{description}</Dialog.Description>
            ) : (
              <Dialog.Description className="visually-hidden">{title}</Dialog.Description>
            )}
          </div>
          <div className="dialog-body">{children}</div>
          {footer ? <div className="dialog-footer">{footer}</div> : null}
          <Dialog.Close asChild>
            <button type="button" className="dialog-close" aria-label="Close">
              ×
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

export function ReasonConfirmModal({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  reason,
  onReasonChange,
  onConfirm,
  confirming,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  confirmLabel?: string
  reason: string
  onReasonChange: (value: string) => void
  onConfirm: () => void
  confirming?: boolean
}) {
  const canConfirm = reason.trim().length > 0 && !confirming
  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      footer={
        <>
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" variant="danger" disabled={!canConfirm} onClick={onConfirm}>
            {confirming ? 'Working…' : confirmLabel}
          </Button>
        </>
      }
    >
      <label className="field">
        <span className="field__label">
          Reason <span className="field__required">*</span>
        </span>
        <textarea
          className="control"
          rows={4}
          value={reason}
          onChange={(event) => onReasonChange(event.target.value)}
          placeholder="Explain why this action is needed for the audit trail."
          autoFocus
        />
      </label>
    </Modal>
  )
}
