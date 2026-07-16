export function ReasoningCard({ text }: { text: string }) {
  return (
    <details className="reasoning-card" style={{ marginBottom: '8px', padding: '8px', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)' }}>
      <summary style={{ cursor: 'pointer', fontWeight: 500, color: 'var(--color-text-secondary)' }}>Thinking...</summary>
      <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px', fontSize: '0.85em', color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>
        {text}
      </pre>
    </details>
  )
}
