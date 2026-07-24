import { useState, isValidElement, type ReactNode } from 'react'

function extractTextContent(node: ReactNode): string {
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractTextContent).join('')
  if (isValidElement(node) && node.props && (node.props as { children?: ReactNode }).children) {
    return extractTextContent((node.props as { children?: ReactNode }).children)
  }
  return ''
}

export function PreBlock({ children, ...props }: any) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const textToCopy = extractTextContent(children)
    if (navigator.clipboard && textToCopy) {
      void navigator.clipboard.writeText(textToCopy).then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }).catch(console.error)
    }
  }

  return (
    <div style={{ position: 'relative', margin: '10px 0' }}>
      <button
        type="button"
        onClick={handleCopy}
        title="Copy code"
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          background: copied ? 'rgba(34, 197, 94, 0.25)' : 'rgba(255, 255, 255, 0.14)',
          border: `1px solid ${copied ? 'rgba(34, 197, 94, 0.5)' : 'rgba(255, 255, 255, 0.25)'}`,
          borderRadius: '6px',
          color: copied ? '#4ade80' : '#f3f4f6',
          padding: '4px 10px',
          fontSize: '0.75rem',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          zIndex: 2,
          fontFamily: 'sans-serif',
          backdropFilter: 'blur(6px)',
          boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
          transition: 'all 0.15s ease'
        }}
      >
        <span style={{ fontSize: '0.85rem' }}>{copied ? '✓' : '📋'}</span>
        <span>{copied ? 'Copied!' : 'Copy'}</span>
      </button>
      <pre
        style={{
          color: '#abb2bf',
          background: '#282c34',
          padding: '12px 14px',
          paddingTop: '32px',
          borderRadius: 6,
          overflowX: 'auto',
          margin: 0,
          fontSize: '0.88rem',
          lineHeight: '1.45'
        }}
        {...props}
      >
        {children}
      </pre>
    </div>
  )
}

export const sharedMarkdownComponents = {
  code: ({children, ...props}: any) => (
    <code style={{ color: '#abb2bf', background: '#282c34', padding: '0.1em 0.3em', borderRadius: 4, fontFamily: 'monospace' }} {...props}>
      {children}
    </code>
  ),
  pre: PreBlock,
  p: ({_node, ...props}: any) => <p style={{margin: '0 0 4px 0'}} {...props} />,
  ul: ({_node, ...props}: any) => <ul style={{margin: '0 0 4px 24px', padding: 0, listStyleType: 'disc'}} {...props} />,
  ol: ({_node, ...props}: any) => <ol style={{margin: '0 0 4px 24px', padding: 0, listStyleType: 'decimal'}} {...props} />,
  li: ({_node, ...props}: any) => <li style={{margin: '2px 0'}} {...props} />,
  a: ({_node, ...props}: any) => <a style={{color: 'var(--color-accent-primary)', textDecoration: 'underline'}} target="_blank" rel="noopener noreferrer" {...props} />
}

export const userMarkdownComponents = {
  ...sharedMarkdownComponents,
  a: ({_node, ...props}: any) => <a style={{color: 'inherit', textDecoration: 'underline'}} target="_blank" rel="noopener noreferrer" {...props} />
}

