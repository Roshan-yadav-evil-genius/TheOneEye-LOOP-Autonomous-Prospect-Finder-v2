import { useState } from 'react'

export interface JsonHighlighterProps {
  data: unknown
  initialCollapsedDepth?: number
}

function JsonTreeNode({
  keyName,
  value,
  isLast = true,
  depth = 0,
  initialCollapsedDepth = 2,
}: {
  keyName?: string
  value: unknown
  isLast?: boolean
  depth?: number
  initialCollapsedDepth?: number
}) {
  const isObject = value !== null && typeof value === 'object' && !Array.isArray(value)
  const isArray = Array.isArray(value)
  const isExpandable = isObject || isArray

  const [isCollapsed, setIsCollapsed] = useState(() => depth >= initialCollapsedDepth)

  const keySpan = keyName !== undefined ? (
    <span style={{ color: '#e06c75', marginRight: '4px' }}>
      "{keyName}":
    </span>
  ) : null

  if (!isExpandable) {
    let valueNode = null
    if (typeof value === 'string') {
      valueNode = <span style={{ color: '#98c379' }}>"{value}"</span>
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      valueNode = <span style={{ color: '#d19a66' }}>{String(value)}</span>
    } else if (value === null) {
      valueNode = <span style={{ color: '#d19a66' }}>null</span>
    } else {
      valueNode = <span style={{ color: '#abb2bf' }}>{String(value)}</span>
    }

    return (
      <div style={{ paddingLeft: depth > 0 ? '16px' : 0, lineHeight: 1.5, fontFamily: 'monospace' }}>
        {keySpan}{valueNode}{!isLast && <span style={{ color: '#abb2bf' }}>,</span>}
      </div>
    )
  }

  const entries = isArray
    ? (value as unknown[]).map((v, i) => ({ key: String(i), val: v }))
    : Object.entries(value as Record<string, unknown>).map(([k, v]) => ({ key: k, val: v }))

  const openChar = isArray ? '[' : '{'
  const closeChar = isArray ? ']' : '}'
  const itemCount = entries.length

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsCollapsed((prev) => !prev)
  }

  if (itemCount === 0) {
    return (
      <div style={{ paddingLeft: depth > 0 ? '16px' : 0, lineHeight: 1.5, fontFamily: 'monospace' }}>
        {keySpan}<span style={{ color: '#abb2bf' }}>{openChar}{closeChar}</span>{!isLast && <span style={{ color: '#abb2bf' }}>,</span>}
      </div>
    )
  }

  return (
    <div style={{ paddingLeft: depth > 0 ? '16px' : 0, lineHeight: 1.5, fontFamily: 'monospace' }}>
      <div
        style={{ display: 'inline-flex', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
        onClick={handleToggle}
      >
        <span
          style={{
            display: 'inline-block',
            width: '14px',
            fontSize: '0.7em',
            color: '#abb2bf',
            marginRight: '2px',
          }}
        >
          {isCollapsed ? '▶' : '▼'}
        </span>
        {keySpan}
        <span style={{ color: '#abb2bf' }}>{openChar}</span>
        {isCollapsed && (
          <span
            style={{
              color: '#5c6370',
              fontStyle: 'italic',
              fontSize: '0.85em',
              marginLeft: '6px',
              marginRight: '6px',
              background: 'rgba(255,255,255,0.06)',
              padding: '1px 6px',
              borderRadius: '3px',
            }}
          >
            {isArray ? `${itemCount} items` : `${itemCount} keys`}
          </span>
        )}
        {isCollapsed && <span style={{ color: '#abb2bf' }}>{closeChar}{!isLast && ','}</span>}
      </div>

      {!isCollapsed && (
        <>
          <div>
            {entries.map((entry, idx) => (
              <JsonTreeNode
                key={entry.key}
                keyName={isArray ? undefined : entry.key}
                value={entry.val}
                isLast={idx === itemCount - 1}
                depth={depth + 1}
                initialCollapsedDepth={initialCollapsedDepth}
              />
            ))}
          </div>
          <div style={{ color: '#abb2bf' }}>
            {closeChar}{!isLast && ','}
          </div>
        </>
      )}
    </div>
  )
}

export function JsonHighlighter({ data, initialCollapsedDepth = 3 }: JsonHighlighterProps) {
  let parsedData = data
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data)
    } catch {
      parsedData = data
    }
  }

  return (
    <div
      style={{
        margin: 0,
        padding: '12px',
        fontSize: '0.85em',
        fontFamily: 'monospace',
        wordBreak: 'break-word',
        color: '#abb2bf',
        background: '#282c34',
        borderRadius: '6px',
        overflowX: 'auto',
      }}
    >
      <JsonTreeNode value={parsedData} initialCollapsedDepth={initialCollapsedDepth} />
    </div>
  )
}
