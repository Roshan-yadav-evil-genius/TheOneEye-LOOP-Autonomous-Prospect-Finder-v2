import { useEffect, useState, useCallback } from 'react'
import { apiClient } from '../../../shared/api/client'
import { Button } from '../../../shared/components/button'

export interface ActionData {
  id: string
  type: string
  description: string
  tool?: string | null
  inputs?: Record<string, any>
  expected_output?: string | null
  status: string
  result?: string | null
  error?: string | null
  execution_time_ms?: number | null
}

export interface StepData {
  id: string
  title: string
  description?: string
  status: string
  result?: string | null
  actions: ActionData[]
}

export interface TaskData {
  id: string
  title: string
  description?: string
  dependencies: string[]
  tools?: string[]
  completion_criteria?: string[]
  expected_output?: string | null
  status: string
  result?: string | null
  steps: StepData[]
}

export interface PhaseData {
  id: string
  title: string
  objective?: string | null
  status: string
  tasks: TaskData[]
}

export interface KnowledgeData {
  findings: string[]
  decisions: string[]
  discovered_entities: string[]
}

export interface ArtifactData {
  id: string
  name: string
  type: string
  path_or_uri?: string | null
  content_summary?: string | null
  created_at: string
}

export interface ResumeData {
  resume_phase?: string | null
  resume_task?: string | null
  resume_step?: string | null
  first_action?: string | null
}

export interface RuntimeData {
  status: string
  current_phase?: string | null
  current_task?: string | null
  current_step?: string | null
  next_action?: ActionData | null
  progress: number
  iteration: number
  checkpoint: number
}

export interface PlanData {
  planner_id: string
  version: number
  goal: string
  objective: string
  success_criteria?: string[]
  constraints?: string[]
  phases: PhaseData[]
  runtime: RuntimeData
  knowledge: KnowledgeData
  resume?: ResumeData | null
  artifacts: ArtifactData[]
  final_report?: string | null
  created_at: string
  updated_at: string
}

interface PlanDashboardProps {
  effortPrefix: string
}

export type DashboardSubTab = 'PLAN' | 'RUNTIME' | 'RESUME' | 'KNOWLEDGE' | 'ARTIFACTS'
const parseDecisionText = (text: string) => {
  const rationaleIndex = text.indexOf('Rationale:')
  let mainPart = text
  let rationalePart = ''
  if (rationaleIndex !== -1) {
    mainPart = text.substring(0, rationaleIndex).trim()
    rationalePart = text.substring(rationaleIndex + 'Rationale:'.length).trim()
  }

  let title = ''
  let description = mainPart

  const colonIdx = mainPart.indexOf(':')
  const dashIdx = mainPart.indexOf(' - ')

  if (colonIdx !== -1 && (dashIdx === -1 || colonIdx < dashIdx) && colonIdx < 90) {
    title = mainPart.substring(0, colonIdx).trim()
    description = mainPart.substring(colonIdx + 1).trim()
  } else if (dashIdx !== -1 && dashIdx < 90) {
    title = mainPart.substring(0, dashIdx).trim()
    description = mainPart.substring(dashIdx + 3).trim()
  }

  return { title, description, rationale: rationalePart, fullText: text }
}

const parseEntityText = (text: string) => {
  const colonIdx = text.indexOf(':')
  let name = ''
  let details = text

  if (colonIdx !== -1 && colonIdx < 70) {
    name = text.substring(0, colonIdx).trim()
    details = text.substring(colonIdx + 1).trim()
  }

  const bulletItems = details
    .split(';')
    .map((s) => s.trim())
    .filter(Boolean)

  return { name, details, bulletItems, fullText: text }
}

export function PlanDashboard({ effortPrefix }: PlanDashboardProps) {
  const [plan, setPlan] = useState<PlanData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<DashboardSubTab>('PLAN')
  const [taskFilter, setTaskFilter] = useState<TaskFilterOption>('ALL')
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({})
  const [expandedActions, setExpandedActions] = useState<Record<string, boolean>>({})
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactData | null>(null)
  const [knowledgeSubTab, setKnowledgeSubTab] = useState<'FINDINGS' | 'DECISIONS' | 'ENTITIES'>('FINDINGS')
  const [knowledgeSearch, setKnowledgeSearch] = useState('')

  const fetchPlan = useCallback(async () => {
    try {
      setError(null)
      const res = await apiClient.get<PlanData>(`/api/v1/efforts/${encodeURIComponent(effortPrefix)}/plan`)
      setPlan(res.data)
    } catch (err: any) {
      setError(err.message || 'Failed to load execution plan')
    } finally {
      setLoading(false)
    }
  }, [effortPrefix])

  useEffect(() => {
    void fetchPlan()
  }, [fetchPlan])

  const toggleTaskExpand = (taskId: string) => {
    setExpandedTasks((prev) => ({ ...prev, [taskId]: !prev[taskId] }))
  }

  const toggleActionExpand = (actionId: string) => {
    setExpandedActions((prev) => ({ ...prev, [actionId]: !prev[actionId] }))
  }

  const copyToClipboard = (text: string, key: string) => {
    void navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const formatTimestamp = (ts?: string | null) => {
    if (!ts) return 'N/A'
    try {
      const d = new Date(ts)
      if (isNaN(d.getTime())) return ts
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return ts
    }
  }

  const getStatusBadgeStyle = (status: string) => {
    const s = (status || '').toLowerCase()
    if (s === 'completed') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-success) 18%, transparent)',
        color: 'var(--color-status-success)',
        border: '1px solid color-mix(in srgb, var(--color-status-success) 40%, transparent)',
      }
    }
    if (s === 'running' || s === 'planning') {
      return {
        bg: 'color-mix(in srgb, var(--color-accent-primary) 18%, transparent)',
        color: 'var(--color-accent-primary)',
        border: '1px solid color-mix(in srgb, var(--color-accent-primary) 45%, transparent)',
      }
    }
    if (s === 'failed') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-danger) 18%, transparent)',
        color: 'var(--color-status-danger)',
        border: '1px solid color-mix(in srgb, var(--color-status-danger) 40%, transparent)',
      }
    }
    if (s === 'blocked' || s === 'waiting') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-warning) 18%, transparent)',
        color: 'var(--color-status-warning)',
        border: '1px solid color-mix(in srgb, var(--color-status-warning) 40%, transparent)',
      }
    }
    return {
      bg: 'var(--color-bg-elevated)',
      color: 'var(--color-text-secondary)',
      border: '1px solid var(--color-border-default)',
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', padding: '3rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              border: '3px solid var(--color-border-default)',
              borderTopColor: 'var(--color-accent-primary)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 12px auto',
            }}
          />
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', margin: 0 }}>
            Loading Planner Execution State...
          </p>
        </div>
      </div>
    )
  }

  if (error || !plan) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-status-danger)', fontWeight: 600, fontSize: '1rem' }}>
          {error || 'Plan data not available'}
        </p>
        <Button variant="outline" onClick={() => void fetchPlan()} style={{ marginTop: '1rem' }}>
          Retry Loading Plan
        </Button>
      </div>
    )
  }

  // Calculate task status aggregates
  let totalTasks = 0
  let completedTasks = 0
  let runningTasks = 0
  let failedTasks = 0
  let pendingTasks = 0

  plan.phases.forEach((phase) => {
    phase.tasks.forEach((t) => {
      totalTasks++
      const s = (t.status || '').toLowerCase()
      if (s === 'completed') completedTasks++
      else if (s === 'running') runningTasks++
      else if (s === 'failed') failedTasks++
      else pendingTasks++
    })
  })

  const runtimeBadge = getStatusBadgeStyle(plan.runtime.status)
  const isExecuting = plan.runtime.status === 'running' || plan.runtime.status === 'planning'

  // Lookup active phase/task/step objects
  let activePhaseObj: PhaseData | undefined
  let activeTaskObj: TaskData | undefined
  let activeStepObj: StepData | undefined

  if (plan.runtime.current_phase) {
    activePhaseObj = plan.phases.find((p) => p.id === plan.runtime.current_phase)
  }
  if (plan.runtime.current_task) {
    for (const p of plan.phases) {
      const found = p.tasks.find((t) => t.id === plan.runtime.current_task)
      if (found) {
        activeTaskObj = found
        if (!activePhaseObj) activePhaseObj = p
        break
      }
    }
  }
  if (plan.runtime.current_step && activeTaskObj) {
    activeStepObj = activeTaskObj.steps.find((s) => s.id === plan.runtime.current_step)
  }

  // Resume state check
  const resumeState = plan.resume
  const hasResumeData = Boolean(
    resumeState &&
      (resumeState.resume_phase || resumeState.resume_task || resumeState.resume_step || resumeState.first_action)
  )

  const totalKnowledgeItems =
    (plan.knowledge.findings?.length || 0) +
    (plan.knowledge.decisions?.length || 0) +
    (plan.knowledge.discovered_entities?.length || 0)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        overflowY: 'auto',
        gap: '1.25rem',
        padding: '1.25rem',
        background: 'var(--color-bg-primary)',
        color: 'var(--color-text-primary)',
        fontFamily: 'inherit',
      }}
    >
      {/* 1. Header & Global Metadata Strip */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          background: 'var(--color-bg-surface)',
          padding: '1.25rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-default)',
          boxShadow: 'var(--shadow-panel)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', minWidth: 0, flex: 1 }}>
            <div
              style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: 'color-mix(in srgb, var(--color-accent-primary) 15%, transparent)',
                border: '1px solid color-mix(in srgb, var(--color-accent-primary) 30%, transparent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.4rem',
                flexShrink: 0,
                marginTop: '2px',
              }}
            >
              🗺️
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <h2
                  style={{
                    margin: 0,
                    fontSize: '1.15rem',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                    color: 'var(--color-text-primary)',
                    lineHeight: 1.35,
                  }}
                >
                  Goal: {plan.goal}
                </h2>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: '999px',
                    background: runtimeBadge.bg,
                    color: runtimeBadge.color,
                    border: runtimeBadge.border,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  {isExecuting && (
                    <span
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: 'currentColor',
                        animation: 'pulse 1.5s infinite',
                      }}
                    />
                  )}
                  {plan.runtime.status}
                </span>
              </div>

              {plan.objective && (
                <div
                  style={{
                    margin: '6px 0 0 0',
                    fontSize: '0.85rem',
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.45,
                  }}
                >
                  <strong style={{ color: 'var(--color-text-primary)' }}>Objective:</strong> {plan.objective}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Button variant="outline" onClick={() => void fetchPlan()} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              🔄 Refresh
            </Button>
          </div>
        </div>

        {/* Header Metadata Chips */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            flexWrap: 'wrap',
            paddingTop: '12px',
            borderTop: '1px solid var(--color-border-default)',
            fontSize: '0.75rem',
          }}
        >
          <span
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Checkpoint: <strong style={{ color: 'var(--color-text-primary)' }}>#{plan.runtime.checkpoint}</strong>
          </span>
          <span
            style={{
              padding: '3px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Iteration: <strong style={{ color: 'var(--color-text-primary)' }}>#{plan.runtime.iteration}</strong>
          </span>

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '14px', color: 'var(--color-text-secondary)' }}>
            <span>Created: <strong style={{ color: 'var(--color-text-primary)' }}>{formatTimestamp(plan.created_at)}</strong></span>
            <span>Updated: <strong style={{ color: 'var(--color-text-primary)' }}>{formatTimestamp(plan.updated_at)}</strong></span>
          </div>
        </div>
      </div>

      {/* 2. Sub-Tabs Navigation Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--color-bg-surface)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-default)',
          boxShadow: 'var(--shadow-panel)',
          flexWrap: 'wrap',
        }}
      >
        {[
          { id: 'PLAN', label: 'Plan', icon: '🗺️', count: `${totalTasks} Tasks` },
          { id: 'RUNTIME', label: 'Runtime', icon: '⚡', badge: plan.runtime.status },
          { id: 'RESUME', label: 'Resume', icon: '🔄', badge: hasResumeData ? 'Active' : 'Idle' },
          { id: 'KNOWLEDGE', label: 'Knowledge', icon: '💡', count: totalKnowledgeItems },
          { id: 'ARTIFACTS', label: 'Artifacts', icon: '📄', count: plan.artifacts.length },
        ].map((tab) => {
          const isActive = activeSubTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSubTab(tab.id as DashboardSubTab)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                border: isActive
                  ? '1px solid var(--color-accent-primary)'
                  : '1px solid var(--color-border-default)',
                background: isActive
                  ? 'var(--color-accent-primary)'
                  : 'var(--color-bg-elevated)',
                color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease-in-out',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 2px 8px color-mix(in srgb, var(--color-accent-primary) 35%, transparent)' : 'none',
              }}
            >
              <span style={{ fontSize: '1rem', lineHeight: 1 }}>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  style={{
                    fontSize: '0.72rem',
                    padding: '2px 8px',
                    borderRadius: '999px',
                    background: isActive
                      ? 'rgba(255, 255, 255, 0.25)'
                      : 'color-mix(in srgb, var(--color-accent-primary) 15%, transparent)',
                    color: isActive ? '#ffffff' : 'var(--color-accent-primary)',
                    fontWeight: 700,
                  }}
                >
                  {tab.count}
                </span>
              )}
              {tab.badge && (
                <span
                  style={{
                    fontSize: '0.68rem',
                    padding: '2px 8px',
                    borderRadius: '999px',
                    background: isActive
                      ? 'rgba(255, 255, 255, 0.25)'
                      : 'var(--color-bg-primary)',
                    color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                    textTransform: 'uppercase',
                    fontWeight: 700,
                    border: isActive ? 'none' : '1px solid var(--color-border-default)',
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* 3. TAB 1: PLAN */}
      {activeSubTab === 'PLAN' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Strategic Context Card */}
          <div
            style={{
              background: 'var(--color-bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-default)',
              boxShadow: 'var(--shadow-panel)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                STRATEGIC GOAL & CONSTRAINTS
              </span>
            </div>

            <div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1.3 }}>
                {plan.goal}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.4, marginTop: '4px' }}>
                {plan.objective}
              </div>
            </div>

            {/* Success Criteria Checklist */}
            {plan.success_criteria && plan.success_criteria.length > 0 && (
              <div style={{ paddingTop: '8px', borderTop: '1px dashed var(--color-border-default)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-status-success)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  🎯 Success Criteria ({plan.success_criteria.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {plan.success_criteria.map((crit, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', fontSize: '0.8rem', color: 'var(--color-text-primary)' }}>
                      <span style={{ color: 'var(--color-status-success)' }}>✓</span>
                      <span style={{ flex: 1, lineHeight: 1.3 }}>{crit}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Operational Constraints */}
            {plan.constraints && plan.constraints.length > 0 && (
              <div style={{ paddingTop: '8px', borderTop: '1px dashed var(--color-border-default)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-status-warning)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  🛡️ Operational Constraints
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {plan.constraints.map((c, idx) => (
                    <span
                      key={idx}
                      style={{
                        fontSize: '0.74rem',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-md)',
                        background: 'color-mix(in srgb, var(--color-status-warning) 12%, transparent)',
                        border: '1px solid color-mix(in srgb, var(--color-status-warning) 30%, transparent)',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      ⚠️ {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Executive Final Report Card (If Present) */}
          {plan.final_report && (
            <div
              style={{
                background: 'var(--color-bg-surface)',
                border: '1px solid color-mix(in srgb, var(--color-status-success) 40%, var(--color-border-default))',
                padding: '1.25rem',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-panel)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>📊</span>
                <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-status-success)' }}>
                  Final Executive Report
                </h3>
              </div>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-primary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                {plan.final_report}
              </p>
            </div>
          )}

          {/* Execution Roadmap & Tasks with Operator Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '10px',
              }}
            >
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
                Execution Roadmap & Tasks
              </h3>

              {/* Status Filter Bar */}
              <div style={{ display: 'flex', gap: '4px', background: 'var(--color-bg-elevated)', padding: '3px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                {(['ALL', 'RUNNING', 'COMPLETED', 'FAILED', 'PENDING'] as TaskFilterOption[]).map((f) => {
                  const isActive = taskFilter === f
                  return (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setTaskFilter(f)}
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        padding: '3px 10px',
                        borderRadius: 'var(--radius-sm)',
                        border: 'none',
                        background: isActive ? 'var(--color-accent-primary)' : 'transparent',
                        color: isActive ? '#fff' : 'var(--color-text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      {f === 'ALL' ? `All (${totalTasks})` : f === 'RUNNING' ? `Running (${runningTasks})` : f === 'COMPLETED' ? `Done (${completedTasks})` : f === 'FAILED' ? `Failed (${failedTasks})` : `Pending (${pendingTasks})`}
                    </button>
                  )
                })}
              </div>
            </div>

            {plan.phases.length === 0 ? (
              <p className="muted" style={{ fontSize: '0.85rem' }}>No phases defined yet in plan.</p>
            ) : (
              plan.phases.map((phase, pIdx) => {
                const phaseBadge = getStatusBadgeStyle(phase.status)

                const filteredTasks = phase.tasks.filter((t) => {
                  if (taskFilter === 'ALL') return true
                  const s = (t.status || '').toUpperCase()
                  if (taskFilter === 'PENDING') return s !== 'RUNNING' && s !== 'COMPLETED' && s !== 'FAILED'
                  return s === taskFilter
                })

                if (taskFilter !== 'ALL' && filteredTasks.length === 0) return null

                return (
                  <div
                    key={phase.id}
                    style={{
                      background: 'var(--color-bg-surface)',
                      border: '1px solid var(--color-border-default)',
                      borderRadius: 'var(--radius-lg)',
                      boxShadow: 'var(--shadow-panel)',
                      overflow: 'hidden',
                    }}
                  >
                    {/* Phase Header */}
                    <div
                      style={{
                        padding: '12px 16px',
                        background: 'var(--color-bg-elevated)',
                        borderBottom: '1px solid var(--color-border-default)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span
                          style={{
                            width: '26px',
                            height: '26px',
                            borderRadius: '50%',
                            background: 'color-mix(in srgb, var(--color-accent-primary) 20%, transparent)',
                            color: 'var(--color-accent-primary)',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {pIdx + 1}
                        </span>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                            {phase.title}
                          </h4>
                          {phase.objective && (
                            <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>{phase.objective}</span>
                          )}
                        </div>
                      </div>

                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '999px',
                          background: phaseBadge.bg,
                          color: phaseBadge.color,
                          border: phaseBadge.border,
                          textTransform: 'uppercase',
                        }}
                      >
                        {phase.status}
                      </span>
                    </div>

                    {/* Tasks List */}
                    <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {filteredTasks.length === 0 ? (
                        <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                          No tasks assigned under this phase matching filter.
                        </p>
                      ) : (
                        filteredTasks.map((task) => {
                          const tBadge = getStatusBadgeStyle(task.status)
                          const isExpanded = !!expandedTasks[task.id]
                          const isActiveTask = task.id === plan.runtime.current_task

                          return (
                            <div
                              key={task.id}
                              style={{
                                background: isActiveTask
                                  ? 'color-mix(in srgb, var(--color-accent-primary) 5%, var(--color-bg-primary))'
                                  : 'var(--color-bg-primary)',
                                border: isActiveTask
                                  ? '2px solid var(--color-accent-primary)'
                                  : '1px solid var(--color-border-default)',
                                borderRadius: 'var(--radius-md)',
                                padding: '14px',
                                boxShadow: isActiveTask ? '0 0 12px color-mix(in srgb, var(--color-accent-primary) 30%, transparent)' : 'none',
                                transition: 'all 0.2s ease',
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                    {isActiveTask && (
                                      <span
                                        style={{
                                          fontSize: '0.65rem',
                                          fontWeight: 800,
                                          padding: '2px 6px',
                                          borderRadius: '4px',
                                          background: 'var(--color-accent-primary)',
                                          color: '#fff',
                                          letterSpacing: '0.04em',
                                        }}
                                      >
                                        ⚡ ACTIVE NOW
                                      </span>
                                    )}

                                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                                      {task.title}
                                    </span>

                                    <span
                                      style={{
                                        fontSize: '0.68rem',
                                        fontWeight: 700,
                                        padding: '2px 6px',
                                        borderRadius: '999px',
                                        background: tBadge.bg,
                                        color: tBadge.color,
                                        border: tBadge.border,
                                        textTransform: 'uppercase',
                                      }}
                                    >
                                      {task.status}
                                    </span>
                                    <code style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>{task.id}</code>
                                  </div>

                                  {task.description && (
                                    <p style={{ margin: '6px 0 0 0', fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                                      {task.description}
                                    </p>
                                  )}

                                  {/* Task Expected Output callout */}
                                  {task.expected_output && (
                                    <div
                                      style={{
                                        marginTop: '8px',
                                        padding: '6px 10px',
                                        background: 'var(--color-bg-elevated)',
                                        borderRadius: 'var(--radius-sm)',
                                        borderLeft: '3px solid var(--color-accent-primary)',
                                        fontSize: '0.78rem',
                                        color: 'var(--color-text-primary)',
                                      }}
                                    >
                                      🎯 <strong>Expected Deliverable:</strong> {task.expected_output}
                                    </div>
                                  )}

                                  {/* Tools Badges & Completion Criteria */}
                                  <div style={{ display: 'flex', gap: '10px', marginTop: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                                    {task.tools && task.tools.length > 0 && (
                                      <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                        <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>Tools:</span>
                                        {task.tools.map((tl) => (
                                          <span
                                            key={tl}
                                            style={{
                                              fontSize: '0.68rem',
                                              background: 'color-mix(in srgb, var(--color-accent-primary) 12%, transparent)',
                                              border: '1px solid color-mix(in srgb, var(--color-accent-primary) 25%, transparent)',
                                              padding: '1px 6px',
                                              borderRadius: 'var(--radius-sm)',
                                              color: 'var(--color-accent-primary)',
                                              fontWeight: 600,
                                            }}
                                          >
                                            🔧 {tl}
                                          </span>
                                        ))}
                                      </div>
                                    )}

                                    {task.dependencies && task.dependencies.length > 0 && (
                                      <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                        <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>Prereqs:</span>
                                        {task.dependencies.map((dep) => (
                                          <span
                                            key={dep}
                                            style={{
                                              fontSize: '0.68rem',
                                              background: 'var(--color-bg-elevated)',
                                              border: '1px solid var(--color-border-default)',
                                              padding: '1px 5px',
                                              borderRadius: 'var(--radius-sm)',
                                              color: 'var(--color-text-primary)',
                                            }}
                                          >
                                            {dep}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {/* Task Final Result */}
                                  {task.result && (
                                    <div
                                      style={{
                                        marginTop: '8px',
                                        padding: '8px 10px',
                                        background: 'color-mix(in srgb, var(--color-status-success) 10%, transparent)',
                                        borderLeft: '3px solid var(--color-status-success)',
                                        borderRadius: 'var(--radius-md)',
                                        fontSize: '0.8rem',
                                        color: 'var(--color-text-primary)',
                                      }}
                                    >
                                      <strong>Task Outcome Result:</strong> {task.result}
                                    </div>
                                  )}
                                </div>

                                {task.steps && task.steps.length > 0 && (
                                  <Button
                                    variant="ghost"
                                    onClick={() => toggleTaskExpand(task.id)}
                                    style={{ fontSize: '0.75rem', padding: '4px 8px', height: 'auto' }}
                                  >
                                    {isExpanded ? '▲ Hide Steps' : `▼ Steps (${task.steps.length})`}
                                  </Button>
                                )}
                              </div>

                              {/* Granular Step & Action Inspector */}
                              {isExpanded && task.steps && task.steps.length > 0 && (
                                <div
                                  style={{
                                    marginTop: '12px',
                                    paddingTop: '12px',
                                    borderTop: '1px dashed var(--color-border-default)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '10px',
                                  }}
                                >
                                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                                    Atomic Steps & Action Execution History
                                  </div>

                                  {task.steps.map((step) => (
                                    <div
                                      key={step.id}
                                      style={{
                                        padding: '10px 12px',
                                        background: 'var(--color-bg-elevated)',
                                        borderRadius: 'var(--radius-md)',
                                        border: '1px solid var(--color-border-default)',
                                      }}
                                    >
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                                          📌 Step: {step.title}
                                        </span>
                                        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: getStatusBadgeStyle(step.status).color }}>
                                          {step.status}
                                        </span>
                                      </div>

                                      {step.description && (
                                        <p style={{ margin: '4px 0 0 0', fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>
                                          {step.description}
                                        </p>
                                      )}

                                      {/* Step Actions Inspector */}
                                      {step.actions && step.actions.length > 0 && (
                                        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                          {step.actions.map((act) => {
                                            const isActExpanded = !!expandedActions[act.id]
                                            const actBadge = getStatusBadgeStyle(act.status)

                                            return (
                                              <div
                                                key={act.id}
                                                style={{
                                                  fontSize: '0.75rem',
                                                  padding: '8px 10px',
                                                  background: 'var(--color-bg-primary)',
                                                  borderRadius: 'var(--radius-md)',
                                                  border: '1px solid var(--color-border-default)',
                                                  display: 'flex',
                                                  flexDirection: 'column',
                                                  gap: '6px',
                                                }}
                                              >
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <span
                                                      style={{
                                                        fontSize: '0.65rem',
                                                        fontWeight: 700,
                                                        padding: '1px 6px',
                                                        borderRadius: '4px',
                                                        background: 'color-mix(in srgb, var(--color-accent-primary) 15%, transparent)',
                                                        color: 'var(--color-accent-primary)',
                                                        textTransform: 'uppercase',
                                                      }}
                                                    >
                                                      {act.type}
                                                    </span>
                                                    <strong style={{ color: 'var(--color-text-primary)' }}>
                                                      {act.tool ? `🔧 ${act.tool}` : act.id}
                                                    </strong>
                                                  </div>

                                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    {act.execution_time_ms != null && (
                                                      <span style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                                                        ⏱️ {act.execution_time_ms.toFixed(0)}ms
                                                      </span>
                                                    )}
                                                    <span
                                                      style={{
                                                        fontSize: '0.65rem',
                                                        fontWeight: 700,
                                                        padding: '1px 6px',
                                                        borderRadius: '999px',
                                                        background: actBadge.bg,
                                                        color: actBadge.color,
                                                      }}
                                                    >
                                                      {act.status}
                                                    </span>
                                                  </div>
                                                </div>

                                                <div style={{ color: 'var(--color-text-primary)', fontSize: '0.78rem' }}>
                                                  {act.description}
                                                </div>

                                                {/* Action Inputs & Output Toggle */}
                                                {(act.inputs || act.result || act.error) && (
                                                  <div>
                                                    <button
                                                      type="button"
                                                      onClick={() => toggleActionExpand(act.id)}
                                                      style={{
                                                        background: 'none',
                                                        border: 'none',
                                                        color: 'var(--color-accent-primary)',
                                                        fontSize: '0.7rem',
                                                        fontWeight: 600,
                                                        cursor: 'pointer',
                                                        padding: 0,
                                                      }}
                                                    >
                                                      {isActExpanded ? '▲ Hide Action Inspector' : '▼ Inspect Inputs / Result Payload'}
                                                    </button>

                                                    {isActExpanded && (
                                                      <div
                                                        style={{
                                                          marginTop: '6px',
                                                          display: 'flex',
                                                          flexDirection: 'column',
                                                          gap: '6px',
                                                          background: 'var(--color-bg-elevated)',
                                                          padding: '8px',
                                                          borderRadius: 'var(--radius-sm)',
                                                          border: '1px solid var(--color-border-default)',
                                                        }}
                                                      >
                                                        {act.inputs && Object.keys(act.inputs).length > 0 && (
                                                          <div>
                                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                                                                ACTION INPUTS
                                                              </span>
                                                              <button
                                                                type="button"
                                                                onClick={() => copyToClipboard(JSON.stringify(act.inputs, null, 2), `inp-${act.id}`)}
                                                                style={{
                                                                  background: 'none',
                                                                  border: 'none',
                                                                  color: 'var(--color-accent-primary)',
                                                                  fontSize: '0.65rem',
                                                                  cursor: 'pointer',
                                                                }}
                                                              >
                                                                {copiedKey === `inp-${act.id}` ? 'Copied!' : 'Copy JSON'}
                                                              </button>
                                                            </div>
                                                            <pre
                                                              style={{
                                                                margin: '4px 0 0 0',
                                                                fontSize: '0.7rem',
                                                                background: 'var(--color-bg-primary)',
                                                                padding: '6px',
                                                                borderRadius: '4px',
                                                                overflowX: 'auto',
                                                                maxHeight: '160px',
                                                                color: 'var(--color-text-primary)',
                                                              }}
                                                            >
                                                              {JSON.stringify(act.inputs, null, 2)}
                                                            </pre>
                                                          </div>
                                                        )}

                                                        {act.result && (
                                                          <div>
                                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--color-status-success)' }}>
                                                                ACTION RESULT
                                                              </span>
                                                              <button
                                                                type="button"
                                                                onClick={() => copyToClipboard(act.result!, `res-${act.id}`)}
                                                                style={{
                                                                  background: 'none',
                                                                  border: 'none',
                                                                  color: 'var(--color-accent-primary)',
                                                                  fontSize: '0.65rem',
                                                                  cursor: 'pointer',
                                                                }}
                                                              >
                                                                {copiedKey === `res-${act.id}` ? 'Copied!' : 'Copy Result'}
                                                              </button>
                                                            </div>
                                                            <pre
                                                              style={{
                                                                margin: '4px 0 0 0',
                                                                fontSize: '0.7rem',
                                                                background: 'var(--color-bg-primary)',
                                                                padding: '6px',
                                                                borderRadius: '4px',
                                                                overflowX: 'auto',
                                                                maxHeight: '160px',
                                                                color: 'var(--color-text-primary)',
                                                                whiteSpace: 'pre-wrap',
                                                              }}
                                                            >
                                                              {act.result}
                                                            </pre>
                                                          </div>
                                                        )}

                                                        {act.error && (
                                                          <div>
                                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--color-status-danger)' }}>
                                                                ERROR STACK TRACE
                                                              </span>
                                                              <button
                                                                type="button"
                                                                onClick={() => copyToClipboard(act.error!, `err-${act.id}`)}
                                                                style={{
                                                                  background: 'none',
                                                                  border: 'none',
                                                                  color: 'var(--color-status-danger)',
                                                                  fontSize: '0.65rem',
                                                                  cursor: 'pointer',
                                                                }}
                                                              >
                                                                {copiedKey === `err-${act.id}` ? 'Copied!' : 'Copy Error'}
                                                              </button>
                                                            </div>
                                                            <pre
                                                              style={{
                                                                margin: '4px 0 0 0',
                                                                fontSize: '0.7rem',
                                                                background: 'color-mix(in srgb, var(--color-status-danger) 10%, var(--color-bg-primary))',
                                                                padding: '6px',
                                                                borderRadius: '4px',
                                                                overflowX: 'auto',
                                                                maxHeight: '160px',
                                                                color: 'var(--color-status-danger)',
                                                                whiteSpace: 'pre-wrap',
                                                              }}
                                                            >
                                                              {act.error}
                                                            </pre>
                                                          </div>
                                                        )}
                                                      </div>
                                                    )}
                                                  </div>
                                                )}
                                              </div>
                                            )
                                          })}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )
                        })
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* 4. TAB 2: RUNTIME */}
      {activeSubTab === 'RUNTIME' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Active Execution Banner (Live Pointer Panel) */}
          <div
            style={{
              background: 'color-mix(in srgb, var(--color-accent-primary) 8%, var(--color-bg-surface))',
              border: '1px solid color-mix(in srgb, var(--color-accent-primary) 40%, var(--color-border-default))',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.05)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.1rem' }}>⚡</span>
                <h3
                  style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    letterSpacing: '0.02em',
                    textTransform: 'uppercase',
                    color: 'var(--color-accent-primary)',
                  }}
                >
                  Currently Executing (Live Pointers)
                </h3>
              </div>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  color: 'var(--color-text-secondary)',
                  background: 'var(--color-bg-elevated)',
                  padding: '2px 8px',
                  borderRadius: '999px',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                Realtime Agent State
              </span>
            </div>

            {/* Active Pointers Grid */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '10px',
              }}
            >
              <div
                style={{
                  background: 'var(--color-bg-surface)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>ACTIVE PHASE</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  {activePhaseObj ? activePhaseObj.title : plan.runtime.current_phase || 'None'}
                </div>
                {plan.runtime.current_phase && (
                  <code style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                    ID: {plan.runtime.current_phase}
                  </code>
                )}
              </div>

              <div
                style={{
                  background: 'var(--color-bg-surface)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid color-mix(in srgb, var(--color-accent-primary) 35%, transparent)',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: 'var(--color-accent-primary)', fontWeight: 600 }}>ACTIVE TASK</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  {activeTaskObj ? activeTaskObj.title : plan.runtime.current_task || 'None'}
                </div>
                {plan.runtime.current_task && (
                  <code style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                    ID: {plan.runtime.current_task}
                  </code>
                )}
              </div>

              <div
                style={{
                  background: 'var(--color-bg-surface)',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>ACTIVE STEP</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  {activeStepObj ? activeStepObj.title : plan.runtime.current_step || 'None'}
                </div>
                {plan.runtime.current_step && (
                  <code style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                    ID: {plan.runtime.current_step}
                  </code>
                )}
              </div>
            </div>

            {/* Queued Next Action Preview Card */}
            {plan.runtime.next_action && (
              <div
                style={{
                  background: 'var(--color-bg-surface)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 14px',
                  border: '1px dashed var(--color-accent-primary)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-accent-primary)' }}>
                    ⏳ QUEUED NEXT ACTION
                  </span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      padding: '1px 6px',
                      borderRadius: '999px',
                      background: 'var(--color-bg-elevated)',
                      border: '1px solid var(--color-border-default)',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    {plan.runtime.next_action.type}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  🔧 <strong>{plan.runtime.next_action.tool || plan.runtime.next_action.type}</strong>: {plan.runtime.next_action.description}
                </div>
                {plan.runtime.next_action.inputs && Object.keys(plan.runtime.next_action.inputs).length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                    <strong>Inputs:</strong>{' '}
                    <code style={{ background: 'var(--color-bg-elevated)', padding: '2px 6px', borderRadius: '4px' }}>
                      {JSON.stringify(plan.runtime.next_action.inputs)}
                    </code>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Hero Progress & Task Breakdown Card */}
          <div
            style={{
              background: 'var(--color-bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-default)',
              boxShadow: 'var(--shadow-panel)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  OVERALL EXECUTION PROGRESS
                </span>
                <span style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-accent-primary)' }}>
                  {plan.runtime.progress.toFixed(0)}%
                </span>
              </div>

              {/* Progress Bar */}
              <div
                style={{
                  width: '100%',
                  height: '12px',
                  background: 'var(--color-bg-elevated)',
                  borderRadius: '999px',
                  overflow: 'hidden',
                  border: '1px solid var(--color-border-default)',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min(100, Math.max(0, plan.runtime.progress))}%`,
                    background: 'var(--color-accent-primary)',
                    borderRadius: '999px',
                    transition: 'width 0.4s ease-in-out',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.82rem', color: 'var(--color-text-secondary)', flexWrap: 'wrap' }}>
              <div>
                <strong style={{ color: 'var(--color-status-success)' }}>{completedTasks}</strong> Completed Tasks
              </div>
              <div>
                <strong style={{ color: 'var(--color-accent-primary)' }}>{runningTasks}</strong> Active Tasks
              </div>
              <div>
                <strong>{pendingTasks}</strong> Pending Tasks
              </div>
              {failedTasks > 0 && (
                <div>
                  <strong style={{ color: 'var(--color-status-danger)' }}>{failedTasks}</strong> Failed Tasks
                </div>
              )}
            </div>
          </div>

          {/* Runtime Detailed Status Card */}
          <div
            style={{
              background: 'var(--color-bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-default)',
              boxShadow: 'var(--shadow-panel)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Detailed Runtime State Metrics
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
              <div style={{ background: 'var(--color-bg-elevated)', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>STATUS</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: runtimeBadge.color, marginTop: '2px' }}>
                  {plan.runtime.status.toUpperCase()}
                </div>
              </div>
              <div style={{ background: 'var(--color-bg-elevated)', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>CHECKPOINT NUMBER</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  #{plan.runtime.checkpoint}
                </div>
              </div>
              <div style={{ background: 'var(--color-bg-elevated)', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>ITERATION NUMBER</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  #{plan.runtime.iteration}
                </div>
              </div>
              <div style={{ background: 'var(--color-bg-elevated)', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>SCHEMA VERSION</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                  v{plan.version}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. TAB 3: RESUME */}
      {activeSubTab === 'RESUME' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Agent State Recovery Checklist */}
          <div
            style={{
              background: hasResumeData
                ? 'color-mix(in srgb, var(--color-status-warning) 10%, var(--color-bg-surface))'
                : 'var(--color-bg-surface)',
              border: hasResumeData
                ? '1px solid color-mix(in srgb, var(--color-status-warning) 40%, var(--color-border-default))'
                : '1px solid var(--color-border-default)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-panel)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>🔄</span>
                <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: hasResumeData ? 'var(--color-status-warning)' : 'var(--color-text-primary)' }}>
                  Agent State Recovery & Restoration Checklist
                </h3>
              </div>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: hasResumeData ? 'color-mix(in srgb, var(--color-status-warning) 20%, transparent)' : 'var(--color-bg-elevated)',
                  color: hasResumeData ? 'var(--color-status-warning)' : 'var(--color-text-secondary)',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                {hasResumeData ? 'RECOVERY DATA PRESENT' : 'NO RECOVERY PENDING'}
              </span>
            </div>

            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
              Saved recovery coordinates enable the Planner agent to seamlessly resume execution after process restarts, interruptions, or context switches.
            </p>

            {hasResumeData ? (
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '6px' }}>
                {resumeState?.resume_phase && (
                  <div style={{ fontSize: '0.8rem', padding: '6px 12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                    Target Phase: <strong style={{ color: 'var(--color-text-primary)' }}>{resumeState.resume_phase}</strong>
                  </div>
                )}
                {resumeState?.resume_task && (
                  <div style={{ fontSize: '0.8rem', padding: '6px 12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                    Target Task: <strong style={{ color: 'var(--color-text-primary)' }}>{resumeState.resume_task}</strong>
                  </div>
                )}
                {resumeState?.resume_step && (
                  <div style={{ fontSize: '0.8rem', padding: '6px 12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                    Target Step: <strong style={{ color: 'var(--color-text-primary)' }}>{resumeState.resume_step}</strong>
                  </div>
                )}
                {resumeState?.first_action && (
                  <div style={{ fontSize: '0.8rem', padding: '6px 12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
                    First Action to Resume: <strong style={{ color: 'var(--color-accent-primary)' }}>{resumeState.first_action}</strong>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)', fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>
                ✓ Clean execution state. No interrupt coordinates recorded for this effort.
              </div>
            )}
          </div>

          {/* Recovery Architecture Info */}
          <div
            style={{
              background: 'var(--color-bg-surface)',
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-default)',
              boxShadow: 'var(--shadow-panel)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              State Recovery Guidelines
            </h4>
            <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: '6px', lineHeight: 1.4 }}>
              <li>Planner checkpoints are persisted automatically after each action execution cycle.</li>
              <li>When resuming, the agent loads the latest checkpoint (<strong>#{plan.runtime.checkpoint}</strong>) and evaluates the <code>resume</code> coordinates.</li>
              <li>If <code>first_action</code> is defined, execution resumes directly from the pending atomic action without repeating completed steps.</li>
            </ul>
          </div>
        </div>
      )}

      {/* 6. TAB 4: KNOWLEDGE */}
      {activeSubTab === 'KNOWLEDGE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Knowledge Sub-Tabs Header Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              flexWrap: 'wrap',
              background: 'var(--color-bg-surface)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border-default)',
              boxShadow: 'var(--shadow-panel)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {[
                {
                  id: 'FINDINGS',
                  label: 'Strategic Findings',
                  icon: '💡',
                  count: plan.knowledge.findings?.length || 0,
                  accentColor: 'var(--color-status-success)',
                },
                {
                  id: 'DECISIONS',
                  label: 'Architectural Decisions',
                  icon: '🎯',
                  count: plan.knowledge.decisions?.length || 0,
                  accentColor: 'var(--color-accent-primary)',
                },
                {
                  id: 'ENTITIES',
                  label: 'Discovered Entities',
                  icon: '🏷️',
                  count: plan.knowledge.discovered_entities?.length || 0,
                  accentColor: 'var(--color-status-warning)',
                },
              ].map((kt) => {
                const isActive = knowledgeSubTab === kt.id
                return (
                  <button
                    key={kt.id}
                    type="button"
                    onClick={() => setKnowledgeSubTab(kt.id as 'FINDINGS' | 'DECISIONS' | 'ENTITIES')}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-md)',
                      border: isActive
                        ? `1px solid ${kt.accentColor}`
                        : '1px solid var(--color-border-default)',
                      background: isActive
                        ? `color-mix(in srgb, ${kt.accentColor} 15%, var(--color-bg-elevated))`
                        : 'var(--color-bg-elevated)',
                      color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease-in-out',
                      boxShadow: isActive ? `0 2px 8px color-mix(in srgb, ${kt.accentColor} 25%, transparent)` : 'none',
                    }}
                  >
                    <span style={{ fontSize: '1rem' }}>{kt.icon}</span>
                    <span>{kt.label}</span>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: isActive
                          ? kt.accentColor
                          : 'var(--color-bg-primary)',
                        color: isActive ? '#ffffff' : kt.accentColor,
                        fontWeight: 700,
                      }}
                    >
                      {kt.count}
                    </span>
                  </button>
                )
              })}
            </div>

            {/* Quick Knowledge Search Filter */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto' }}>
              <div style={{ position: 'relative', width: '220px' }}>
                <input
                  type="text"
                  placeholder="Filter knowledge..."
                  value={knowledgeSearch}
                  onChange={(e) => setKnowledgeSearch(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 12px 6px 28px',
                    fontSize: '0.78rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border-default)',
                    background: 'var(--color-bg-primary)',
                    color: 'var(--color-text-primary)',
                    outline: 'none',
                  }}
                />
                <span
                  style={{
                    position: 'absolute',
                    left: '8px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    fontSize: '0.75rem',
                    color: 'var(--color-text-secondary)',
                    pointerEvents: 'none',
                  }}
                >
                  🔍
                </span>
                {knowledgeSearch && (
                  <button
                    type="button"
                    onClick={() => setKnowledgeSearch('')}
                    style={{
                      position: 'absolute',
                      right: '6px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--color-text-secondary)',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* SUB-TAB 1: STRATEGIC FINDINGS */}
          {knowledgeSubTab === 'FINDINGS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {(() => {
                const findingsList = (plan.knowledge.findings || []).filter((f) =>
                  !knowledgeSearch || f.toLowerCase().includes(knowledgeSearch.toLowerCase())
                )

                if (findingsList.length === 0) {
                  return (
                    <div
                      style={{
                        background: 'var(--color-bg-surface)',
                        padding: '3rem 1.5rem',
                        borderRadius: 'var(--radius-lg)',
                        border: '1px solid var(--color-border-default)',
                        textAlign: 'center',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      <div style={{ fontSize: '2rem', marginBottom: '8px' }}>💡</div>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {knowledgeSearch ? 'No matching findings found' : 'No Strategic Findings Recorded'}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.82rem', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                        {knowledgeSearch
                          ? `No findings matching "${knowledgeSearch}".`
                          : 'Strategic findings are recorded automatically as subagents extract market insights and strategic intelligence.'}
                      </p>
                    </div>
                  )
                }

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    {findingsList.map((finding, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--color-bg-surface)',
                          padding: '1.15rem 1.25rem',
                          borderRadius: 'var(--radius-lg)',
                          border: '1px solid var(--color-border-default)',
                          borderLeft: '4px solid var(--color-status-success)',
                          boxShadow: 'var(--shadow-panel)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              background: 'color-mix(in srgb, var(--color-status-success) 15%, transparent)',
                              color: 'var(--color-status-success)',
                              border: '1px solid color-mix(in srgb, var(--color-status-success) 30%, transparent)',
                              letterSpacing: '0.04em',
                            }}
                          >
                            FINDING #{String(idx + 1).padStart(2, '0')}
                          </span>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(finding, `find-${idx}`)}
                            style={{
                              background: 'var(--color-bg-elevated)',
                              border: '1px solid var(--color-border-default)',
                              color: 'var(--color-text-secondary)',
                              fontSize: '0.72rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              padding: '3px 8px',
                              borderRadius: 'var(--radius-sm)',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                          >
                            {copiedKey === `find-${idx}` ? '✓ Copied' : '📋 Copy Text'}
                          </button>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--color-text-primary)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
                          {finding}
                        </p>
                      </div>
                    ))}
                  </div>
                )
              })()}
            </div>
          )}

          {/* SUB-TAB 2: ARCHITECTURAL DECISIONS */}
          {knowledgeSubTab === 'DECISIONS' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {(() => {
                const decisionsList = (plan.knowledge.decisions || []).filter((d) =>
                  !knowledgeSearch || d.toLowerCase().includes(knowledgeSearch.toLowerCase())
                )

                if (decisionsList.length === 0) {
                  return (
                    <div
                      style={{
                        background: 'var(--color-bg-surface)',
                        padding: '3rem 1.5rem',
                        borderRadius: 'var(--radius-lg)',
                        border: '1px solid var(--color-border-default)',
                        textAlign: 'center',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🎯</div>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {knowledgeSearch ? 'No matching decisions found' : 'No Architectural Decisions Recorded'}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.82rem', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                        {knowledgeSearch
                          ? `No decisions matching "${knowledgeSearch}".`
                          : 'Key architectural decisions and tool-selection logic will appear here as research progresses.'}
                      </p>
                    </div>
                  )
                }

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {decisionsList.map((dec, idx) => {
                      const parsed = parseDecisionText(dec)
                      return (
                        <div
                          key={idx}
                          style={{
                            background: 'var(--color-bg-surface)',
                            padding: '1.25rem',
                            borderRadius: 'var(--radius-lg)',
                            border: '1px solid var(--color-border-default)',
                            borderLeft: '4px solid var(--color-accent-primary)',
                            boxShadow: 'var(--shadow-panel)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                          }}
                        >
                          {/* Decision Header */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                              <span
                                style={{
                                  fontSize: '0.7rem',
                                  fontWeight: 700,
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  background: 'color-mix(in srgb, var(--color-accent-primary) 15%, transparent)',
                                  color: 'var(--color-accent-primary)',
                                  border: '1px solid color-mix(in srgb, var(--color-accent-primary) 30%, transparent)',
                                  letterSpacing: '0.04em',
                                }}
                              >
                                DECISION #{String(idx + 1).padStart(2, '0')}
                              </span>
                              {parsed.title && (
                                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                                  {parsed.title}
                                </h4>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={() => copyToClipboard(dec, `dec-${idx}`)}
                              style={{
                                background: 'var(--color-bg-elevated)',
                                border: '1px solid var(--color-border-default)',
                                color: 'var(--color-text-secondary)',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                                padding: '3px 8px',
                                borderRadius: 'var(--radius-sm)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                            >
                              {copiedKey === `dec-${idx}` ? '✓ Copied' : '📋 Copy Decision'}
                            </button>
                          </div>

                          {/* Decision Content */}
                          <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--color-text-primary)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
                            {parsed.description}
                          </p>

                          {/* Rationale Block */}
                          {parsed.rationale && (
                            <div
                              style={{
                                marginTop: '4px',
                                padding: '10px 14px',
                                background: 'color-mix(in srgb, var(--color-accent-primary) 8%, var(--color-bg-primary))',
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid color-mix(in srgb, var(--color-accent-primary) 20%, transparent)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '4px',
                              }}
                            >
                              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--color-accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <span>💡</span>
                                <span>Rationale & Strategy</span>
                              </div>
                              <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                                {parsed.rationale}
                              </p>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )
              })()}
            </div>
          )}

          {/* SUB-TAB 3: DISCOVERED ENTITIES */}
          {knowledgeSubTab === 'ENTITIES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {(() => {
                const entitiesList = (plan.knowledge.discovered_entities || []).filter((e) =>
                  !knowledgeSearch || e.toLowerCase().includes(knowledgeSearch.toLowerCase())
                )

                if (entitiesList.length === 0) {
                  return (
                    <div
                      style={{
                        background: 'var(--color-bg-surface)',
                        padding: '3rem 1.5rem',
                        borderRadius: 'var(--radius-lg)',
                        border: '1px solid var(--color-border-default)',
                        textAlign: 'center',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🏷️</div>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {knowledgeSearch ? 'No matching entities found' : 'No Discovered Entities Recorded'}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.82rem', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
                        {knowledgeSearch
                          ? `No entities matching "${knowledgeSearch}".`
                          : 'Discovered company profiles, data sources, and industry entities will be listed here.'}
                      </p>
                    </div>
                  )
                }

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {entitiesList.map((entityStr, idx) => {
                      const parsed = parseEntityText(entityStr)
                      const isDetailed = parsed.bulletItems.length > 1 || entityStr.length > 80

                      if (!isDetailed) {
                        // Short entity badge / tag
                        return (
                          <div
                            key={idx}
                            style={{
                              background: 'var(--color-bg-surface)',
                              padding: '10px 14px',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--color-border-default)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                            }}
                          >
                            <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                              🏷️ {entityStr}
                            </span>
                            <button
                              type="button"
                              onClick={() => copyToClipboard(entityStr, `ent-${idx}`)}
                              style={{
                                background: 'var(--color-bg-elevated)',
                                border: '1px solid var(--color-border-default)',
                                color: 'var(--color-text-secondary)',
                                fontSize: '0.72rem',
                                cursor: 'pointer',
                                padding: '2px 8px',
                                borderRadius: '4px',
                              }}
                            >
                              {copiedKey === `ent-${idx}` ? '✓ Copied' : 'Copy'}
                            </button>
                          </div>
                        )
                      }

                      // Detailed Entity Profile Card
                      return (
                        <div
                          key={idx}
                          style={{
                            background: 'var(--color-bg-surface)',
                            padding: '1.25rem',
                            borderRadius: 'var(--radius-lg)',
                            border: '1px solid var(--color-border-default)',
                            borderLeft: '4px solid var(--color-status-warning)',
                            boxShadow: 'var(--shadow-panel)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '10px',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                              <span
                                style={{
                                  fontSize: '0.7rem',
                                  fontWeight: 700,
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  background: 'color-mix(in srgb, var(--color-status-warning) 15%, transparent)',
                                  color: 'var(--color-status-warning)',
                                  border: '1px solid color-mix(in srgb, var(--color-status-warning) 30%, transparent)',
                                  letterSpacing: '0.04em',
                                }}
                              >
                                ENTITY #{String(idx + 1).padStart(2, '0')}
                              </span>
                              {parsed.name && (
                                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                                  {parsed.name}
                                </h4>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={() => copyToClipboard(entityStr, `ent-${idx}`)}
                              style={{
                                background: 'var(--color-bg-elevated)',
                                border: '1px solid var(--color-border-default)',
                                color: 'var(--color-text-secondary)',
                                fontSize: '0.72rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                                padding: '3px 8px',
                                borderRadius: 'var(--radius-sm)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                            >
                              {copiedKey === `ent-${idx}` ? '✓ Copied' : '📋 Copy Profile'}
                            </button>
                          </div>

                          {/* Render Bullet Items / Structured Profile */}
                          {parsed.bulletItems.length > 1 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '2px' }}>
                              {parsed.bulletItems.map((item, bIdx) => (
                                <div
                                  key={bIdx}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '8px',
                                    fontSize: '0.85rem',
                                    color: 'var(--color-text-primary)',
                                    lineHeight: 1.45,
                                    background: 'var(--color-bg-primary)',
                                    padding: '8px 12px',
                                    borderRadius: 'var(--radius-md)',
                                    border: '1px solid var(--color-border-default)',
                                  }}
                                >
                                  <span style={{ color: 'var(--color-status-warning)', fontWeight: 700, fontSize: '0.9rem' }}>•</span>
                                  <span style={{ flex: 1 }}>{item}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--color-text-primary)', lineHeight: 1.55 }}>
                              {parsed.details}
                            </p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )
              })()}
            </div>
          )}
        </div>
      )}

      {/* 7. TAB 5: ARTIFACTS */}
      {activeSubTab === 'ARTIFACTS' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
            Registered Artifacts Inspector ({plan.artifacts.length})
          </h3>

          {plan.artifacts.length === 0 ? (
            <div
              style={{
                background: 'var(--color-bg-surface)',
                padding: '1.25rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-secondary)',
                fontSize: '0.85rem',
              }}
            >
              No artifacts generated yet for this effort.
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '1rem',
              }}
            >
              {plan.artifacts.map((art) => (
                <div
                  key={art.id}
                  style={{
                    background: 'var(--color-bg-surface)',
                    padding: '1.25rem',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--color-border-default)',
                    boxShadow: 'var(--shadow-panel)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      📄 {art.name}
                    </span>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '999px',
                        background: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-default)',
                        color: 'var(--color-text-secondary)',
                        textTransform: 'uppercase',
                      }}
                    >
                      {art.type}
                    </span>
                  </div>

                  {art.content_summary && (
                    <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                      {art.content_summary}
                    </p>
                  )}

                  {art.path_or_uri && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        background: 'var(--color-bg-primary)',
                        padding: '4px 8px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border-default)',
                      }}
                    >
                      <code
                        style={{
                          fontSize: '0.68rem',
                          color: 'var(--color-text-secondary)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {art.path_or_uri}
                      </code>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(art.path_or_uri!, `art-${art.id}`)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--color-accent-primary)',
                          fontSize: '0.68rem',
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                          marginLeft: '6px',
                        }}
                      >
                        {copiedKey === `art-${art.id}` ? 'Copied!' : 'Copy Path'}
                      </button>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                      {formatTimestamp(art.created_at)}
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => setSelectedArtifact(art)}
                      style={{ fontSize: '0.72rem', padding: '2px 8px', height: 'auto' }}
                    >
                      👁️ View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal / Inspector Drawer for Viewing Selected Artifact */}
      {selectedArtifact && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
          onClick={() => setSelectedArtifact(null)}
        >
          <div
            style={{
              background: 'var(--color-bg-surface)',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem',
              maxWidth: '600px',
              width: '100%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                📄 {selectedArtifact.name}
              </h3>
              <Button variant="ghost" onClick={() => setSelectedArtifact(null)}>
                ✕
              </Button>
            </div>

            <div>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: 'var(--color-bg-elevated)',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                Category: {selectedArtifact.type}
              </span>
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '6px' }}>
                Created: {formatTimestamp(selectedArtifact.created_at)}
              </p>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                CONTENT SUMMARY
              </div>
              <div
                style={{
                  marginTop: '4px',
                  padding: '10px',
                  background: 'var(--color-bg-primary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-default)',
                  fontSize: '0.82rem',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {selectedArtifact.content_summary || 'No summary available.'}
              </div>
            </div>

            {selectedArtifact.path_or_uri && (
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
                  STORAGE LOCATION / URI
                </div>
                <div
                  style={{
                    marginTop: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--color-bg-primary)',
                    padding: '8px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border-default)',
                  }}
                >
                  <code style={{ fontSize: '0.75rem', wordBreak: 'break-all' }}>
                    {selectedArtifact.path_or_uri}
                  </code>
                  <Button
                    variant="outline"
                    onClick={() => copyToClipboard(selectedArtifact.path_or_uri!, 'modal-path')}
                    style={{ fontSize: '0.72rem', padding: '2px 8px', whiteSpace: 'nowrap', height: 'auto' }}
                  >
                    {copiedKey === 'modal-path' ? 'Copied!' : 'Copy'}
                  </Button>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <Button variant="secondary" onClick={() => setSelectedArtifact(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
