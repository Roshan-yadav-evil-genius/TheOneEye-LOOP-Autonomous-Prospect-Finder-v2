import React from 'react'

export const sharedMarkdownComponents = {
  code: ({children, ...props}: any) => (
    <code style={{ color: '#abb2bf', background: '#282c34', padding: '0.1em 0.3em', borderRadius: 4, fontFamily: 'monospace' }} {...props}>
      {children}
    </code>
  ),
  pre: ({children, ...props}: any) => (
    <pre style={{ color: '#abb2bf', background: '#282c34', padding: 12, borderRadius: 6, overflowX: 'auto', margin: '4px 0' }} {...props}>
      {children}
    </pre>
  ),
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
