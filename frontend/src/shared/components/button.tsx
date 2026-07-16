import { Slot } from '@radix-ui/react-slot'
import { clsx } from 'clsx'
import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: 'primary' | 'ghost' | 'danger'
}

export function Button({
  asChild = false,
  className,
  variant = 'primary',
  ...props
}: PropsWithChildren<ButtonProps>) {
  const Component = asChild ? Slot : 'button'
  return <Component className={clsx('button', `button--${variant}`, className)} {...props} />
}
