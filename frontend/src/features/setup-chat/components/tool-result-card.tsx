import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { JsonHighlighter } from './json-highlighter'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { sharedMarkdownComponents, sharedRemarkPlugins } from './shared-markdown-components'

export function ToolResultCard({ name, content, rules }: { name: string; content: string; rules?: ToolCustomizationRuleRead[] }) {
  const [showMarkdown, setShowMarkdown] = useState(false)
  const matchedRule = rules?.find(r => name.startsWith(r.tool_name_prefix))
  
  const backgroundColor = matchedRule?.response_color || 'var(--color-bg-elevated)'
  
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
        Result: {name}
        <button 
          onClick={(e) => {
            e.preventDefault()
            setShowMarkdown(!showMarkdown)
          }}
          style={{
            marginLeft: 'auto',
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
