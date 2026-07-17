import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { JsonHighlighter } from './json-highlighter'

export function ToolCallCard({ name, args, rules }: { name: string; args: unknown; rules?: ToolCustomizationRuleRead[] }) {
  const matchedRule = rules?.find(r => name.startsWith(r.tool_name_prefix))
  
  const backgroundColor = matchedRule?.request_color || 'var(--color-bg-elevated)'
  
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
        Call: {name}
      </summary>
      <div style={{ marginTop: '8px', overflowX: 'auto' }}>
        <JsonHighlighter data={args} />
      </div>
    </details>
  )
}
