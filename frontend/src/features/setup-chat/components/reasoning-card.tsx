import ReactMarkdown from 'react-markdown'
import { sharedMarkdownComponents, sharedRemarkPlugins } from './shared-markdown-components'

function getAgentBadgeStyle(agent?: string) {
  const agentLower = (agent || '').toLowerCase()
  if (agentLower.includes('evaluator')) {
    return { background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }
  }
  if (agentLower.includes('sales') || agentLower.includes('brain')) {
    return { background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }
  }
  return { background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' }
}

export function ReasoningCard({ text, agent }: { text: string; agent?: string }) {
  const badgeStyle = getAgentBadgeStyle(agent)
  const agentLabel = agent || 'Planner Agent'

  return (
    <details className="reasoning-card" style={{ padding: '8px 12px', background: 'var(--color-bg-subtle)', borderLeft: '3px solid var(--color-accent-primary)', borderRadius: '0 var(--radius-md) var(--radius-md) 0', width: '100%' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-secondary)', fontSize: '0.9em', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '1.2em', fontStyle: 'normal' }}>💭</span>
        <span style={{ fontStyle: 'italic' }}>Thinking</span>
        <span style={{
          marginLeft: 'auto',
          fontSize: '0.72rem',
          fontWeight: 600,
          padding: '2px 8px',
          borderRadius: '12px',
          ...badgeStyle
        }}>
          {agentLabel}
        </span>
      </summary>
      <div style={{ marginTop: '8px', fontSize: '0.85em', color: 'var(--color-text-primary)' }}>
        <ReactMarkdown remarkPlugins={sharedRemarkPlugins} components={sharedMarkdownComponents as any}>
          {text}
        </ReactMarkdown>
      </div>
    </details>
  )
}
