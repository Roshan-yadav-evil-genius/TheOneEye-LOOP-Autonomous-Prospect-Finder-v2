export function ToolResultCard({ name, content }: { name: string; content: string }) {
  return (
    <details className="tool-result-card" style={{ marginBottom: '8px', padding: '8px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-primary)' }}>✅ Result: {name}</summary>
      <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px', fontSize: '0.85em', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
        {content}
      </pre>
    </details>
  )
}
