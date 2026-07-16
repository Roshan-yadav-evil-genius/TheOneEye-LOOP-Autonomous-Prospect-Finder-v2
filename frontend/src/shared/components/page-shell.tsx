import type { PropsWithChildren } from 'react'
import { Link } from 'react-router-dom'

import { useTheme } from '../hooks/use-theme'
import { Button } from './button'

export function PageShell({ children }: PropsWithChildren) {
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="page-shell">
      <nav className="top-nav" aria-label="Global navigation">
        <Link className="top-nav__brand" to="/">
          LOOP
        </Link>
        <div className="top-nav__links">
          <Link className="top-nav__link" to="/orgs">
            Organizations
          </Link>
          <Link className="top-nav__link" to="/orgs/new">
            New organization
          </Link>
          <Link className="top-nav__link" to="/admin">
            Admin
          </Link>
        </div>
        <Button variant="ghost" onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
          {theme === 'dark' ? 'Light' : 'Dark'}
        </Button>
      </nav>
      <main className="page-content">{children}</main>
    </div>
  )
}
