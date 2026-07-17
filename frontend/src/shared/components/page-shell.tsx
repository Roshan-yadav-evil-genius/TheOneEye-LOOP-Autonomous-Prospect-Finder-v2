import type { PropsWithChildren } from 'react'
import { Link, NavLink } from 'react-router-dom'

import { useTheme } from '../hooks/use-theme'

export function PageShell({ children }: PropsWithChildren) {
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="page-shell">
      <nav
        aria-label="Global navigation"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 2rem',
          minHeight: '4.5rem',
          background: 'color-mix(in srgb, var(--color-bg-surface) 80%, transparent)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--color-border-default)',
          boxShadow: '0 4px 20px -2px rgba(0,0,0,0.05)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <style>{`
          .premium-nav-link {
            color: var(--color-text-secondary);
            font-size: 1.05rem;
            font-weight: 700;
            text-decoration: none;
            position: relative;
            padding: 0.5rem 0;
            transition: color 0.2s ease;
          }
          .premium-nav-link:hover,
          .premium-nav-link.active {
            color: var(--color-text-primary);
          }
          .premium-nav-link::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: var(--color-accent-primary);
            transform: scaleX(0);
            transform-origin: right;
            transition: transform 0.3s cubic-bezier(0.65, 0, 0.35, 1);
            border-radius: 2px;
          }
          .premium-nav-link:hover::after,
          .premium-nav-link.active::after {
            transform: scaleX(1);
            transform-origin: left;
          }
          .theme-toggle-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 1px solid var(--color-border-default);
            background: var(--color-bg-elevated);
            cursor: pointer;
            transition: all 0.2s ease;
            color: var(--color-text-primary);
          }
          .theme-toggle-btn:hover {
            background: color-mix(in srgb, var(--color-border-default) 50%, var(--color-bg-elevated));
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
          }
        `}</style>
        
        {/* Left section: LOOP Logo and Name */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}>
          <img src="/static/LOOP.png" alt="LOOP Logo" style={{ height: '36px', objectFit: 'contain' }} />
          <span style={{ fontSize: '1.5rem', fontWeight: '800', letterSpacing: '0.05em', color: 'var(--color-text-primary)' }}>LOOP</span>
        </Link>

        {/* Center section: Navigation Links */}
        <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '2.5rem' }}>
          <NavLink 
            to="/orgs" 
            className={({ isActive }) => `premium-nav-link ${isActive ? 'active' : ''}`}
          >
            Organizations
          </NavLink>
          <NavLink 
            to="/admin" 
            className={({ isActive }) => `premium-nav-link ${isActive ? 'active' : ''}`}
          >
            Admin
          </NavLink>
        </div>

        {/* Right section: Powered by, Logo, Theme Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--color-text-primary)' }}>
              Powered by
            </span>
            <img src="/static/TheOneEye.png" alt="TheOneEye Logo" style={{ height: '28px', objectFit: 'contain' }} />
          </div>

          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="theme-toggle-btn"
          >
            {theme === 'dark' ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
            )}
          </button>
        </div>
      </nav>
      <main className="page-content">{children}</main>
    </div>
  )
}
