import { clsx } from 'clsx'
import type { ButtonHTMLAttributes, MouseEvent, PropsWithChildren } from 'react'
import { Link } from 'react-router-dom'

type IconButtonBase = {
  label: string
  className?: string
}

export function IconButton({
  label,
  className,
  children,
  ...props
}: PropsWithChildren<IconButtonBase & ButtonHTMLAttributes<HTMLButtonElement>>) {
  return (
    <button
      type="button"
      className={clsx('icon-button', className)}
      aria-label={label}
      title={label}
      {...props}
    >
      {children}
    </button>
  )
}

export function IconLink({
  label,
  to,
  className,
  children,
  onClick,
}: PropsWithChildren<
  IconButtonBase & {
    to: string
    onClick?: (event: MouseEvent<HTMLAnchorElement>) => void
  }
>) {
  return (
    <Link
      to={to}
      className={clsx('icon-button', className)}
      aria-label={label}
      title={label}
      onClick={onClick}
    >
      {children}
    </Link>
  )
}

export function EditIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path
        d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}
