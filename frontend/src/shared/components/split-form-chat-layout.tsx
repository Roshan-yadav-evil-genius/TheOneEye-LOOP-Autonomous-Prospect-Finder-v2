import React from 'react'
import { Breadcrumbs, type BreadcrumbItem } from './breadcrumbs'

export interface SplitFormChatLayoutProps {
  title: string
  subtitle?: string
  breadcrumbs?: BreadcrumbItem[]
  actions?: React.ReactNode
  leftPanel: React.ReactNode
  rightPanel: React.ReactNode
  leftPanelStyle?: React.CSSProperties
  rightPanelStyle?: React.CSSProperties
}

export function SplitFormChatLayout({
  title,
  subtitle,
  breadcrumbs,
  actions,
  leftPanel,
  rightPanel,
  leftPanelStyle,
  rightPanelStyle,
}: SplitFormChatLayoutProps) {
  return (
    <div className="split-layout-container">
      {/* Top Header & Breadcrumb Bar */}
      <div className="split-layout-header">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <div style={{ marginBottom: '8px' }}>
            <Breadcrumbs items={breadcrumbs} />
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.02em' }}>{title}</h1>
            {subtitle && <p className="muted" style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>{subtitle}</p>}
          </div>
          {actions && <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>{actions}</div>}
        </div>
      </div>

      {/* Separator Line */}
      <hr className="split-layout-separator" />

      {/* Main Full-Height Content Area */}
      <div className="split-panel-grid">
        <div className="split-panel-left" style={leftPanelStyle}>
          {leftPanel}
        </div>
        <div className="split-panel-right" style={rightPanelStyle}>
          {rightPanel}
        </div>
        </div>
    </div>
  )
}
