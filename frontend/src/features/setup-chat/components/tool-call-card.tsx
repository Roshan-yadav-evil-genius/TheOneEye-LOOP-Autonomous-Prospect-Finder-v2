import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { JsonHighlighter } from './json-highlighter'

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

export function ToolCallCard({ name, args, agent, rules }: { name: string; args: unknown; agent?: string; rules?: ToolCustomizationRuleRead[] }) {
  const matchedRule = rules?.find(r => name.startsWith(r.tool_name_prefix))
  
  const backgroundColor = matchedRule?.request_color || 'var(--color-bg-elevated)'
  const badgeStyle = getAgentBadgeStyle(agent)
  const agentLabel = agent || 'Planner Agent'
  
  return (
    <details className="tool-call-card" style={{ padding: '8px', background: backgroundColor, border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)', width: '100%' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        {matchedRule?.icon_url ? (
          <>
            <img 
              src={matchedRule.icon_url} 
              alt="icon" 
              style={{ width: 16, height: 16 }} 
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                if (e.currentTarget.nextElementSibling) {
                  e.currentTarget.nextElementSibling.removeAttribute('hidden');
                }
              }}
            />
            <span hidden style={{ fontSize: '1.2em' }}>🛠️</span>
          </>
        ) : <span style={{ fontSize: '1.2em' }}>🛠️</span>}
        <span>Call: {name}</span>
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
      <div style={{ marginTop: '8px', overflowX: 'auto' }}>
        <JsonHighlighter data={args} />
      </div>
    </details>
  )
}
