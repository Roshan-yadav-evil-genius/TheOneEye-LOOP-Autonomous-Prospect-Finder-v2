import type { PropsWithChildren, ReactNode } from 'react'

interface CardProps {
  title?: ReactNode
  className?: string
}

export function Card({ children, className = '', title }: PropsWithChildren<CardProps>) {
  return (
    <section className={`card ${className}`.trim()}>
      {title ? (
        <header className="card__header">
          <h2 className="card__title">{title}</h2>
        </header>
      ) : null}
      <div className="card__body">{children}</div>
    </section>
  )
}
