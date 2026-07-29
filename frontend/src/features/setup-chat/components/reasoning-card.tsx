import ReactMarkdown from 'react-markdown'
import { sharedMarkdownComponents, sharedRemarkPlugins } from './shared-markdown-components'

export function ReasoningCard({ text }: { text: string }) {
  return (
    <details className="reasoning-card" style={{ padding: '8px 12px', background: 'var(--color-bg-subtle)', borderLeft: '3px solid var(--color-accent-primary)', borderRadius: '0 var(--radius-md) var(--radius-md) 0', width: '100%' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-secondary)', fontSize: '0.9em', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '1.2em', fontStyle: 'normal' }}>💭</span>
        <span style={{ fontStyle: 'italic' }}>Thinking</span>
      </summary>
      <div style={{ marginTop: '8px', fontSize: '0.85em', color: 'var(--color-text-primary)' }}>
        <ReactMarkdown remarkPlugins={sharedRemarkPlugins} components={sharedMarkdownComponents as any}>
          {text}
        </ReactMarkdown>
      </div>
    </details>
  )
}
