import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { JsonHighlighter } from './json-highlighter'
import { useState } from 'react'
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

export function ToolResultCard({ name, content, agent, rules }: { name: string; content: string; agent?: string; rules?: ToolCustomizationRuleRead[] }) {
  const [showMarkdown, setShowMarkdown] = useState(false)
  const matchedRule = rules?.find(r => name.startsWith(r.tool_name_prefix))
  
  const backgroundColor = matchedRule?.response_color || 'var(--color-bg-elevated)'
  const badgeStyle = getAgentBadgeStyle(agent)
  const agentLabel = agent || 'Planner Agent'
  
  // Try to parse content as JSON for better highlighting, fallback to string
  let parsedContent: unknown = content
  try {
    parsedContent = JSON.parse(content)
  } catch {
    // If it's not valid JSON, we just pass the string to JsonHighlighter
  }
  
  return (
    <details className="tool-result-card" style={{ padding: '8px', background: backgroundColor, border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)', width: '100%' }}>
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
            <span hidden style={{ fontSize: '1.2em' }}>⚙️</span>
          </>
        ) : <span style={{ fontSize: '1.2em' }}>⚙️</span>}
        <span>Result: {name}</span>
        <span style={{
          marginLeft: 'auto',
          marginRight: '8px',
          fontSize: '0.72rem',
          fontWeight: 600,
          padding: '2px 8px',
          borderRadius: '12px',
          ...badgeStyle
        }}>
          {agentLabel}
        </span>
        <button 
          onClick={(e) => {
            e.preventDefault()
            setShowMarkdown(!showMarkdown)
          }}
          style={{
            background: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-default)',
            color: 'var(--color-text-secondary)',
            borderRadius: '4px',
            padding: '2px 8px',
            fontSize: '0.8em',
            cursor: 'pointer'
          }}
        >
          {showMarkdown ? 'Show Raw' : 'Show Markdown'}
        </button>
      </summary>
      <div style={{ marginTop: '8px', overflowX: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {showMarkdown ? (
          <div className="markdown-chat" style={{ color: 'var(--color-text-primary)', wordBreak: 'break-word', fontSize: '0.9em' }}>
            <ReactMarkdown remarkPlugins={sharedRemarkPlugins} components={sharedMarkdownComponents as any}>
              {content}
            </ReactMarkdown>
          </div>
        ) : (
          <JsonHighlighter data={parsedContent} />
        )}
      </div>
    </details>
  )
}
