import * as Dialog from '@radix-ui/react-dialog'
import type { PropsWithChildren, ReactNode } from 'react'

export function Drawer({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
}: PropsWithChildren<{
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  footer?: ReactNode
}>) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="drawer-content">
          <div className="drawer-header">
            <Dialog.Title className="dialog-title">{title}</Dialog.Title>
            {description ? (
              <Dialog.Description className="dialog-description">{description}</Dialog.Description>
            ) : (
              <Dialog.Description className="visually-hidden">{title}</Dialog.Description>
            )}
            <Dialog.Close asChild>
              <button type="button" className="dialog-close" aria-label="Close">
                ×
              </button>
            </Dialog.Close>
          </div>
          <div className="drawer-body">{children}</div>
          {footer ? <div className="drawer-footer">{footer}</div> : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
