import { useState } from 'react'
import type { StateSnapshotRead } from '../api/setup-chat-api-client'
import { JsonHighlighter } from './json-highlighter'

export interface StateSnapshotListProps {
  snapshots: StateSnapshotRead[]
  loading: boolean
  onRefresh?: () => void
}

export function StateSnapshotList({ snapshots, loading, onRefresh }: StateSnapshotListProps) {
  const [collapsedSteps, setCollapsedSteps] = useState<Record<number, boolean>>({})
  const [allCollapsed, setAllCollapsed] = useState<boolean>(false)

  const toggleStep = (stepIndex: number) => {
    setCollapsedSteps((prev) => ({ ...prev, [stepIndex]: !prev[stepIndex] }))
  }

  const toggleAll = () => {
    const nextState = !allCollapsed
    setAllCollapsed(nextState)
    const newCollapsedMap: Record<number, boolean> = {}
    snapshots.forEach((s) => {
      newCollapsedMap[s.step_index] = nextState
    })
    setCollapsedSteps(newCollapsedMap)
  }

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        ⏳ Loading state history snapshots…
      </div>
    )
  }

  if (snapshots.length === 0) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        <p style={{ margin: 0, fontSize: '0.95rem' }}>📭 No state snapshots found for this thread/namespace.</p>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            style={{
              marginTop: '12px',
              padding: '6px 14px',
              background: 'var(--color-accent-primary)',
              color: 'var(--color-accent-foreground)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontSize: '0.825rem',
            }}
          >
            ↺ Refresh State History
          </button>
        )}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.825rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
          State Snapshots ({snapshots.length} steps chronologically)
        </span>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={toggleAll}
            style={{
              padding: '4px 10px',
              background: 'var(--color-bg-elevated)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontSize: '0.775rem',
            }}
          >
            {allCollapsed ? '▶ Expand All' : '▼ Collapse All'}
          </button>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              style={{
                padding: '4px 10px',
                background: 'var(--color-bg-elevated)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border-default)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontSize: '0.775rem',
              }}
            >
              ↺ Refresh
            </button>
          )}
        </div>
      </div>

      {snapshots.map((snapshot) => {
        const isCollapsed = collapsedSteps[snapshot.step_index] || false
        const keysCount = Object.keys(snapshot.values || {}).length

        return (
          <div
            key={snapshot.step_index}
            style={{
              display: 'flex',
              flexDirection: 'column',
              background: 'var(--color-bg-subtle)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
            }}
          >
            {/* Step Header */}
            <div
              onClick={() => toggleStep(snapshot.step_index)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--color-bg-elevated)',
                cursor: 'pointer',
                userSelect: 'none',
                borderBottom: isCollapsed ? 'none' : '1px solid var(--color-border-default)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: 'var(--color-accent-primary)',
                    color: 'var(--color-accent-foreground)',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                  }}
                >
                  Step #{snapshot.step_index}
                </span>

                {snapshot.checkpoint_ns && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      padding: '2px 6px',
                      background: 'var(--color-bg-subtle)',
                      borderRadius: '4px',
                      color: 'var(--color-text-muted)',
                    }}
                  >
                    📦 {snapshot.checkpoint_ns}
                  </span>
                )}

                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  {keysCount} {keysCount === 1 ? 'state key' : 'state keys'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {snapshot.next && snapshot.next.length > 0 && (
                  <span
                    style={{
                      fontSize: '0.725rem',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: 'var(--color-status-info, #1e3a8a)',
                      color: '#93c5fd',
                      fontFamily: 'monospace',
                    }}
                  >
                    Next: {snapshot.next.join(', ')}
                  </span>
                )}
                <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>{isCollapsed ? '▶ Expand' : '▼ Collapse'}</span>
              </div>
            </div>

            {/* Step Body */}
            {!isCollapsed && (
              <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {/* State Snapshot JSON Values */}
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                    State Values (snapshot.values):
                  </div>
                  <JsonHighlighter data={snapshot.values} />
                </div>

                {/* Metadata info if available */}
                {snapshot.metadata && Object.keys(snapshot.metadata).length > 0 && (
                  <details style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 500 }}>Metadata & Writes</summary>
                    <div style={{ marginTop: '4px' }}>
                      <JsonHighlighter data={snapshot.metadata} />
                    </div>
                  </details>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
