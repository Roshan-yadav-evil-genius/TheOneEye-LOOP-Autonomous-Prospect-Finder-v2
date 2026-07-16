export function ToolCallCard({ name, args }: { name: string; args: unknown }) {
  return (
    <details className="tool-call-card" style={{ marginBottom: '8px', padding: '8px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-primary)' }}>🔧 Call: {name}</summary>
      <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px', fontSize: '0.85em', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
        {JSON.stringify(args, null, 2)}
      </pre>
    </details>
  )
}
