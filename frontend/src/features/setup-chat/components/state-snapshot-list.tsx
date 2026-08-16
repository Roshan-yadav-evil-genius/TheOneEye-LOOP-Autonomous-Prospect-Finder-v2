import { useState } from 'react'
import type { StateSnapshotRead } from '../api/setup-chat-api-client'
import { JsonHighlighter } from './json-highlighter'

export interface StateSnapshotListProps {
  snapshots: StateSnapshotRead[]
  loading: boolean
  onRefresh?: () => void
  onRetryCheckpoint?: (config: Record<string, any>) => void
}

export function getCheckpointId(snapshot: StateSnapshotRead): string | null {
  return snapshot.config?.configurable?.checkpoint_id || snapshot.checkpoint?.id || snapshot.checkpoint_id || null
}

export function getCheckpointNs(snapshot: StateSnapshotRead): string | null {
  return snapshot.config?.configurable?.checkpoint_ns || snapshot.metadata?.checkpoint_ns || snapshot.checkpoint_ns || null
}

export function getStepIndex(snapshot: StateSnapshotRead): number {
  return snapshot.step_index ?? snapshot.metadata?.step ?? 0
}

export function getSnapshotValues(snapshot: StateSnapshotRead): Record<string, any> {
  return snapshot.checkpoint?.channel_values || snapshot.values || {}
}

export function getSnapshotTimestamp(snapshot: StateSnapshotRead): string | null {
  return snapshot.checkpoint?.ts || snapshot.metadata?.created_at || snapshot.created_at || null
}

function extractNodeFromChannel(channel: unknown): string | null {
  if (typeof channel !== 'string') return null
  if (channel.startsWith('branch:to:')) return channel.slice('branch:to:'.length).trim() || null
  if (channel.startsWith('branch:to_')) return channel.slice('branch:to_'.length).trim() || null
  return null
}

export function getNextNodeFromSnapshot(snapshot: StateSnapshotRead): { name: string; isComplete: boolean } {
  // 1. Check channel_values
  const channelValues = snapshot.checkpoint?.channel_values || snapshot.values || {}
  for (const key of Object.keys(channelValues)) {
    const nodeName = extractNodeFromChannel(key)
    if (nodeName) return { name: nodeName, isComplete: false }
  }

  // 2. Check pending_writes 3-tuples: [task_id, channel, value]
  const pendingWrites = snapshot.pending_writes || snapshot.checkpoint?.pending_writes || []
  if (Array.isArray(pendingWrites)) {
    for (const write of pendingWrites) {
      if (Array.isArray(write)) {
        const nodeName = extractNodeFromChannel(write[1])
        if (nodeName) return { name: nodeName, isComplete: false }
      }
    }
  }

  // // 3. Fallback
  return { name: 'Completed / End of Graph', isComplete: true }
}

export interface ToolSubGroup {
  id: string
  subNamespace: string
  snapshots: StateSnapshotRead[]
  minStep: number
  maxStep: number
}

export type GroupItem =
  | { kind: 'step'; snapshot: StateSnapshotRead }
  | { kind: 'tool_group'; toolGroup: ToolSubGroup }

export interface PrimaryNamespaceGroup {
  id: string
  namespace: string | null
  label: string
  minStep: number
  maxStep: number
  totalSteps: number
  items: GroupItem[]
}

function formatTimestamp(ts?: string | null): string | null {
  if (!ts) return null
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) {
      const num = Number(ts)
      if (!isNaN(num)) {
        const dateFromNum = new Date(num > 1e11 ? num : num * 1000)
        return dateFromNum.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      }
      return ts
    }
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
}

export function StateSnapshotList({ snapshots, loading, onRefresh, onRetryCheckpoint }: StateSnapshotListProps) {
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({})
  const [collapsedToolGroups, setCollapsedToolGroups] = useState<Record<string, boolean>>({})
  const [collapsedSteps, setCollapsedSteps] = useState<Record<number, boolean>>({})
  const [allCollapsed, setAllCollapsed] = useState<boolean>(true)

  const toggleGroup = (groupId: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [groupId]: !(prev[groupId] ?? true) }))
  }

  const toggleToolGroup = (toolGroupId: string) => {
    setCollapsedToolGroups((prev) => ({ ...prev, [toolGroupId]: !(prev[toolGroupId] ?? true) }))
  }

  const toggleStep = (stepIndex: number) => {
    setCollapsedSteps((prev) => ({ ...prev, [stepIndex]: !(prev[stepIndex] ?? true) }))
  }

  // Build hierarchical primary groups & nested tool sub-groups
  const groups: PrimaryNamespaceGroup[] = []
  let currentPrimary: PrimaryNamespaceGroup | null = null
  let currentToolGroup: ToolSubGroup | null = null
  let groupIndex = 0

  snapshots.forEach((snapshot) => {
    const ns = getCheckpointNs(snapshot) || ''
    const parts = ns.split('|')
    const parentNs = parts[0] || null
    const subNs = parts.slice(1).join('|') || null

    const primaryKey = parentNs || '__root__'

    if (!currentPrimary || currentPrimary.namespace !== parentNs) {
      currentToolGroup = null
      groupIndex += 1
      const groupId = `${primaryKey}::${groupIndex}`
      const label = parentNs ? `📦 ${parentNs}` : '🌐 Root / Main Thread'
      const stepIdx = getStepIndex(snapshot)
      currentPrimary = {
        id: groupId,
        namespace: parentNs,
        label,
        minStep: stepIdx,
        maxStep: stepIdx,
        totalSteps: 0,
        items: [],
      }
      groups.push(currentPrimary)
    }

    const stepIdx = getStepIndex(snapshot)
    currentPrimary.maxStep = Math.max(currentPrimary.maxStep, stepIdx)
    currentPrimary.minStep = Math.min(currentPrimary.minStep, stepIdx)
    currentPrimary.totalSteps += 1

    if (!subNs) {
      currentToolGroup = null
      currentPrimary.items.push({ kind: 'step', snapshot })
    } else {
      const toolGroupId = `${currentPrimary.id}::${subNs}`
      if (!currentToolGroup || currentToolGroup.id !== toolGroupId) {
        currentToolGroup = {
          id: toolGroupId,
          subNamespace: subNs,
          snapshots: [snapshot],
          minStep: snapshot.step_index,
          maxStep: snapshot.step_index,
        }
        currentPrimary.items.push({ kind: 'tool_group', toolGroup: currentToolGroup })
      } else {
        currentToolGroup.snapshots.push(snapshot)
        currentToolGroup.maxStep = Math.max(currentToolGroup.maxStep, snapshot.step_index)
        currentToolGroup.minStep = Math.min(currentToolGroup.minStep, snapshot.step_index)
      }
    }
  })

  const toggleAll = () => {
    const nextState = !allCollapsed
    setAllCollapsed(nextState)

    const newCollapsedGroups: Record<string, boolean> = {}
    const newCollapsedToolGroups: Record<string, boolean> = {}
    groups.forEach((g) => {
      newCollapsedGroups[g.id] = nextState
      g.items.forEach((item) => {
        if (item.kind === 'tool_group') {
          newCollapsedToolGroups[item.toolGroup.id] = nextState
        }
      })
    })
    setCollapsedGroups(newCollapsedGroups)
    setCollapsedToolGroups(newCollapsedToolGroups)

    const newCollapsedSteps: Record<number, boolean> = {}
    snapshots.forEach((s) => {
      newCollapsedSteps[s.step_index] = nextState
    })
    setCollapsedSteps(newCollapsedSteps)
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

  // Render step helper
  const renderStepCard = (snapshot: StateSnapshotRead) => {
    const stepIdx = getStepIndex(snapshot)
    const isStepCollapsed = collapsedSteps[stepIdx] ?? true
    const values = getSnapshotValues(snapshot)
    const keysCount = Object.keys(values).length
    const cpId = getCheckpointId(snapshot)
    const ts = getSnapshotTimestamp(snapshot)
    const nextNodeInfo = getNextNodeFromSnapshot(snapshot)

    return (
      <div
        key={stepIdx}
        style={{
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border-default)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
        }}
      >
          {/* Step Header */}
          <div
            onClick={() => toggleStep(stepIdx)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 14px',
              background: 'var(--color-bg-subtle)',
              cursor: 'pointer',
              userSelect: 'none',
              borderBottom: isStepCollapsed ? 'none' : '1px solid var(--color-border-default)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
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
                Step #{stepIdx}
              </span>

              {cpId && (
                <span
                  title={`Checkpoint ID: ${cpId}`}
                  style={{
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    padding: '2px 6px',
                    background: 'var(--color-bg-elevated)',
                    border: '1px solid var(--color-border-default)',
                    borderRadius: '4px',
                    color: 'var(--color-accent-primary, #3b82f6)',
                    fontWeight: 600,
                  }}
                >
                  🔑 {cpId}
                </span>
              )}

              {ts && (
                <span
                  title={`Created at: ${ts}`}
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-text-muted)',
                    fontFamily: 'monospace',
                  }}
                >
                  🕒 {formatTimestamp(ts)}
                </span>
              )}

              {onRetryCheckpoint && (snapshot.config || cpId) && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    const targetConfig = snapshot.config || {
                      configurable: {
                        checkpoint_id: cpId,
                        checkpoint_ns: getCheckpointNs(snapshot) || '',
                      },
                    }
                    onRetryCheckpoint(targetConfig)
                  }}
                  title="Fork & Retry execution from this checkpoint snapshot"
                  style={{
                    fontSize: '0.725rem',
                    padding: '2px 8px',
                    background: 'var(--color-bg-elevated)',
                    color: 'var(--color-accent-primary, #3b82f6)',
                    border: '1px solid var(--color-border-default)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 600,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  🔁 Fork & Retry
                </button>
              )}

              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                {keysCount} {keysCount === 1 ? 'state key' : 'state keys'}
              </span>
            </div>
          </div>

        {/* Step Body */}
        {!isStepCollapsed && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* State Snapshot JSON Values */}
            <details style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 500 }}>State Values (channel_values)</summary>
              <div style={{ marginTop: '4px' }}>
                <JsonHighlighter data={values} />
              </div>
            </details>

            {/* Metadata, Parent Config & Pending Writes */}
            {(() => {
              const extraInfo: Record<string, any> = {}
              if (snapshot.metadata && Object.keys(snapshot.metadata).length > 0) {
                extraInfo.metadata = snapshot.metadata
              }
              if (snapshot.parent_config && Object.keys(snapshot.parent_config).length > 0) {
                extraInfo.parent_config = snapshot.parent_config
              }
              if (snapshot.pending_writes && snapshot.pending_writes.length > 0) {
                extraInfo.pending_writes = snapshot.pending_writes
              }

              if (Object.keys(extraInfo).length === 0) return null

              return (
                <details style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: 500 }}>Metadata, Parent Config & Writes</summary>
                  <div style={{ marginTop: '4px' }}>
                    <JsonHighlighter data={extraInfo} />
                  </div>
                </details>
              )
            })()}

            {/* Next Node to Execute Banner (Placed at Bottom) */}
            <div
              style={{
                padding: '8px 12px',
                borderRadius: 'var(--radius-md, 6px)',
                background: nextNodeInfo.isComplete
                  ? 'rgba(34, 197, 94, 0.08)'
                  : 'rgba(59, 130, 246, 0.08)',
                border: nextNodeInfo.isComplete
                  ? '1px solid rgba(34, 197, 94, 0.25)'
                  : '1px solid rgba(59, 130, 246, 0.25)',
                color: nextNodeInfo.isComplete
                  ? 'var(--color-success, #22c55e)'
                  : 'var(--color-accent-primary, #3b82f6)',
                fontSize: '0.8rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              {nextNodeInfo.isComplete ? (
                <span>🏁 Status: Execution Complete</span>
              ) : (
                <span>
                  🎯 Next Node to Execute:{' '}
                  <code
                    style={{
                      fontFamily: 'monospace',
                      fontWeight: 700,
                      background: 'var(--color-bg-elevated, rgba(0, 0, 0, 0.2))',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid var(--color-border-default, rgba(255, 255, 255, 0.1))',
                      color: 'var(--color-accent-primary, #3b82f6)',
                    }}
                  >
                    {nextNodeInfo.name}
                  </code>
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingBottom: '16px' }}>
      {/* Top Header Summary & Global Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.825rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>
          State Snapshots ({snapshots.length} total steps across {groups.length} {groups.length === 1 ? 'namespace group' : 'namespace groups'})
        </span>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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

      {/* Render Primary Namespace Groups */}
      {groups.map((group) => {
        const isGroupCollapsed = collapsedGroups[group.id] ?? true
        const stepRangeText =
          group.minStep === group.maxStep
            ? `Step #${group.minStep}`
            : `Steps #${group.minStep} – #${group.maxStep}`

        return (
          <div
            key={group.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-lg, 8px)',
              overflow: 'hidden',
              boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
            }}
          >
            {/* Group Card Header */}
            <div
              onClick={() => toggleGroup(group.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: group.namespace
                  ? 'rgba(59, 130, 246, 0.08)'
                  : 'rgba(255, 255, 255, 0.03)',
                cursor: 'pointer',
                userSelect: 'none',
                borderBottom: isGroupCollapsed ? 'none' : '1px solid var(--color-border-default)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <span
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    fontFamily: group.namespace ? 'monospace' : 'inherit',
                    color: group.namespace ? 'var(--color-accent-primary, #60a5fa)' : 'var(--color-text-primary)',
                  }}
                >
                  {group.label}
                </span>

                <span
                  style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: 'var(--color-bg-subtle)',
                    border: '1px solid var(--color-border-default)',
                    fontSize: '0.75rem',
                    color: 'var(--color-text-muted)',
                    fontWeight: 600,
                  }}
                >
                  {group.totalSteps} {group.totalSteps === 1 ? 'step' : 'steps'} ({stepRangeText})
                </span>
              </div>
            </div>

            {/* Group Card Body: Items (Direct Steps or Nested Tool Groups) */}
            {!isGroupCollapsed && (
              <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', background: 'var(--color-bg-subtle)' }}>
                {group.items.map((item, idx) => {
                  if (item.kind === 'step') {
                    return renderStepCard(item.snapshot)
                  }

                  // Render Nested Tool Sub-Group
                  const toolGroup = item.toolGroup
                  const isToolCollapsed = collapsedToolGroups[toolGroup.id] ?? true
                  const toolStepRange =
                    toolGroup.minStep === toolGroup.maxStep
                      ? `Step #${toolGroup.minStep}`
                      : `Steps #${toolGroup.minStep} – #${toolGroup.maxStep}`

                  return (
                    <div
                      key={toolGroup.id || idx}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        background: 'rgba(245, 158, 11, 0.05)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        margin: '4px 0',
                      }}
                    >
                      {/* Tool Sub-Group Header */}
                      <div
                        onClick={() => toggleToolGroup(toolGroup.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 14px',
                          background: 'rgba(245, 158, 11, 0.1)',
                          cursor: 'pointer',
                          userSelect: 'none',
                          borderBottom: isToolCollapsed ? 'none' : '1px solid rgba(245, 158, 11, 0.2)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                          <span
                            style={{
                              fontSize: '0.825rem',
                              fontWeight: 700,
                              fontFamily: 'monospace',
                              color: '#fbbf24',
                            }}
                          >
                            🛠️ Subagent Tool: {toolGroup.subNamespace}
                          </span>

                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '12px',
                              background: 'var(--color-bg-elevated)',
                              border: '1px solid rgba(245, 158, 11, 0.3)',
                              fontSize: '0.725rem',
                              color: '#d97706',
                              fontWeight: 600,
                            }}
                          >
                            {toolGroup.snapshots.length} {toolGroup.snapshots.length === 1 ? 'step' : 'steps'} ({toolStepRange})
                          </span>
                        </div>
                      </div>

                      {/* Tool Sub-Group Body: Child Step Cards */}
                      {!isToolCollapsed && (
                        <div style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {toolGroup.snapshots.map((subSnapshot) => renderStepCard(subSnapshot))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
