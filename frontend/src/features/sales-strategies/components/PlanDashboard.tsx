import React, { useEffect, useState } from 'react'
import { apiClient } from '../../../shared/api/client'
import { Button } from '../../../shared/components/button'

export interface ActionData {
  id: string
  type: string
  description: string
  tool?: string | null
  inputs?: Record<string, any>
  status: string
  result?: string | null
  error?: string | null
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

export interface PlanData {
  planner_id: string
  version: number
  goal: string
  objective: string
  phases: PhaseData[]
  runtime: {
    status: string
    current_phase?: string | null
    current_task?: string | null
    current_step?: string | null
    progress: number
  }
  knowledge: KnowledgeData
  artifacts: ArtifactData[]
  final_report?: string | null
  created_at: string
  updated_at: string
}

interface PlanDashboardProps {
  effortPrefix: string
}

export function PlanDashboard({ effortPrefix }: PlanDashboardProps) {
  const [plan, setPlan] = useState<PlanData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({})

  const fetchPlan = async () => {
    try {
      setError(null)
      const res = await apiClient.get<PlanData>(`/api/v1/efforts/${encodeURIComponent(effortPrefix)}/plan`)
      setPlan(res.data)
    } catch (err: any) {
      setError(err.message || 'Failed to load execution plan')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchPlan()
  }, [effortPrefix])

  // Auto-refresh every 5 seconds if status is running/planning
  useEffect(() => {
    if (!autoRefresh || !plan || plan.runtime.status === 'completed' || plan.runtime.status === 'failed') {
      return
    }
    const interval = setInterval(() => {
      void fetchPlan()
    }, 5000)
    return () => clearInterval(interval)
  }, [autoRefresh, effortPrefix, plan?.runtime.status])

  const toggleTaskExpand = (taskId: string) => {
    setExpandedTasks((prev) => ({ ...prev, [taskId]: !prev[taskId] }))
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', padding: '2rem' }}>
        <p className="muted" style={{ fontSize: '0.9rem' }}>Loading Plan Execution State...</p>
      </div>
    )
  }

  if (error || !plan) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-status-danger)', fontWeight: 600 }}>{error || 'Plan data not available'}</p>
        <Button variant="outline" style={{ marginTop: '1rem' }} onClick={() => void fetchPlan()}>
          Retry Loading Plan
        </Button>
      </div>
    )
  }

  // Calculate aggregates
  let totalTasks = 0
  let completedTasks = 0
  let runningTasks = 0
  let failedTasks = 0

  plan.phases.forEach((phase) => {
    phase.tasks.forEach((t) => {
      totalTasks++
      if (t.status === 'completed') completedTasks++
      else if (t.status === 'running') runningTasks++
      else if (t.status === 'failed') failedTasks++
    })
  })

  const getStatusBadgeStyle = (status: string) => {
    const s = status.toLowerCase()
    if (s === 'completed') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-success) 14%, transparent)',
        color: 'var(--color-status-success)',
        border: '1px solid color-mix(in srgb, var(--color-status-success) 35%, transparent)',
      }
    }
    if (s === 'running') {
      return {
        bg: 'color-mix(in srgb, var(--color-accent-primary) 16%, transparent)',
        color: 'var(--color-accent-primary)',
        border: '1px solid color-mix(in srgb, var(--color-accent-primary) 40%, transparent)',
      }
    }
    if (s === 'failed') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-danger) 14%, transparent)',
        color: 'var(--color-status-danger)',
        border: '1px solid color-mix(in srgb, var(--color-status-danger) 35%, transparent)',
      }
    }
    if (s === 'blocked') {
      return {
        bg: 'color-mix(in srgb, var(--color-status-warning) 14%, transparent)',
        color: 'var(--color-status-warning)',
        border: '1px solid color-mix(in srgb, var(--color-status-warning) 35%, transparent)',
      }
    }
    return {
      bg: 'var(--color-bg-elevated)',
      color: 'var(--color-text-secondary)',
      border: '1px solid var(--color-border-default)',
    }
  }

  const runtimeStatusStyle = getStatusBadgeStyle(plan.runtime.status)

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
      }}
    >
      {/* Top Header & Controls */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          background: 'var(--color-bg-surface)',
          padding: '1rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-default)',
          boxShadow: 'var(--shadow-panel)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '1.5rem', lineHeight: 1 }}>🗺️</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
                Plan Execution Dashboard
              </h2>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '3px 9px',
                  borderRadius: '999px',
                  background: runtimeStatusStyle.bg,
                  color: runtimeStatusStyle.color,
                  border: runtimeStatusStyle.border,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                {plan.runtime.status}
              </span>
            </div>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
              Planner ID: <code style={{ fontSize: '0.75rem', color: 'var(--color-text-primary)' }}>{plan.planner_id}</code>
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ cursor: 'pointer', accentColor: 'var(--color-accent-primary)' }}
            />
            Auto-refresh (5s)
          </label>
          <Button variant="outline" size="sm" onClick={() => void fetchPlan()}>
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Hero Progress & Goal Section */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* Progress Card */}
        <div
          style={{
            background: 'var(--color-bg-surface)',
            padding: '1.25rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            boxShadow: 'var(--shadow-panel)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                OVERALL PROGRESS
              </span>
              <span style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--color-accent-primary)' }}>
                {plan.runtime.progress}%
              </span>
            </div>

            {/* Standard Project Progress Bar */}
            <div
              style={{
                width: '100%',
                height: '10px',
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

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
            <div>
              <strong style={{ color: 'var(--color-status-success)' }}>{completedTasks}</strong> Completed
            </div>
            <div>
              <strong style={{ color: 'var(--color-accent-primary)' }}>{runningTasks}</strong> Active
            </div>
            <div>
              <strong>{totalTasks - completedTasks - runningTasks - failedTasks}</strong> Pending
            </div>
            {failedTasks > 0 && (
              <div>
                <strong style={{ color: 'var(--color-status-danger)' }}>{failedTasks}</strong> Failed
              </div>
            )}
          </div>
        </div>

        {/* Goal & Objective Card */}
        <div
          style={{
            background: 'var(--color-bg-surface)',
            padding: '1.25rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            boxShadow: 'var(--shadow-panel)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            STRATEGIC GOAL
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1.3 }}>
            {plan.goal}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', lineHeight: 1.4, marginTop: '2px' }}>
            {plan.objective}
          </div>
        </div>
      </div>

      {/* KPI Strip (Standard Project Metric Layout) */}
      <div className="kpi-strip" style={{ margin: 0 }}>
        <div className="kpi-strip__item">
          <p className="kpi-strip__label">Phases</p>
          <p className="kpi-strip__value">{plan.phases.length}</p>
        </div>
        <div className="kpi-strip__item">
          <p className="kpi-strip__label">Total Tasks</p>
          <p className="kpi-strip__value">{totalTasks}</p>
        </div>
        <div className="kpi-strip__item">
          <p className="kpi-strip__label">Findings</p>
          <p className="kpi-strip__value" style={{ color: 'var(--color-status-success)' }}>{plan.knowledge.findings.length}</p>
        </div>
        <div className="kpi-strip__item">
          <p className="kpi-strip__label">Decisions</p>
          <p className="kpi-strip__value" style={{ color: 'var(--color-accent-primary)' }}>{plan.knowledge.decisions.length}</p>
        </div>
        <div className="kpi-strip__item">
          <p className="kpi-strip__label">Artifacts</p>
          <p className="kpi-strip__value" style={{ color: 'var(--color-status-info)' }}>{plan.artifacts.length}</p>
        </div>
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
              Final Plan Executive Report
            </h3>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--color-text-primary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
            {plan.final_report}
          </p>
        </div>
      )}

      {/* Execution Roadmap & Phases */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
          Execution Roadmap & Phases
        </h3>

        {plan.phases.length === 0 ? (
          <p className="muted" style={{ fontSize: '0.85rem' }}>No phases defined yet in plan.</p>
        ) : (
          plan.phases.map((phase, pIdx) => {
            const phaseBadge = getStatusBadgeStyle(phase.status)
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
                        width: '24px',
                        height: '24px',
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
                      <h4 style={{ margin: 0, fontSize: '0.925rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
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
                <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {phase.tasks.length === 0 ? (
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                      No tasks assigned under this phase yet.
                    </p>
                  ) : (
                    phase.tasks.map((task) => {
                      const tBadge = getStatusBadgeStyle(task.status)
                      const isExpanded = !!expandedTasks[task.id]

                      return (
                        <div
                          key={task.id}
                          style={{
                            background: 'var(--color-bg-primary)',
                            border: '1px solid var(--color-border-default)',
                            borderRadius: 'var(--radius-md)',
                            padding: '12px',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
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
                                <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                                  {task.description}
                                </p>
                              )}

                              {task.dependencies && task.dependencies.length > 0 && (
                                <div style={{ display: 'flex', gap: '4px', marginTop: '6px', flexWrap: 'wrap' }}>
                                  <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>Depends on:</span>
                                  {task.dependencies.map((dep) => (
                                    <span
                                      key={dep}
                                      style={{
                                        fontSize: '0.68rem',
                                        background: 'var(--color-bg-elevated)',
                                        border: '1px solid var(--color-border-default)',
                                        padding: '1px 5px',
                                        borderRadius: 'var(--radius-md)',
                                        color: 'var(--color-text-primary)',
                                      }}
                                    >
                                      {dep}
                                    </span>
                                  ))}
                                </div>
                              )}

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
                                  <strong>Output Result:</strong> {task.result}
                                </div>
                              )}
                            </div>

                            {task.steps && task.steps.length > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleTaskExpand(task.id)}
                                style={{ fontSize: '0.75rem', padding: '2px 6px', height: 'auto' }}
                              >
                                {isExpanded ? '▲ Hide Steps' : `▼ Steps (${task.steps.length})`}
                              </Button>
                            )}
                          </div>

                          {/* Expanded Steps & Actions */}
                          {isExpanded && task.steps && task.steps.length > 0 && (
                            <div
                              style={{
                                marginTop: '10px',
                                paddingTop: '10px',
                                borderTop: '1px dashed var(--color-border-default)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '8px',
                              }}
                            >
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                                Steps & Actions
                              </span>
                              {task.steps.map((step) => (
                                <div
                                  key={step.id}
                                  style={{
                                    padding: '8px 10px',
                                    background: 'var(--color-bg-elevated)',
                                    borderRadius: 'var(--radius-md)',
                                    border: '1px solid var(--color-border-default)',
                                  }}
                                >
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                                      📌 {step.title}
                                    </span>
                                    <span style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>{step.status}</span>
                                  </div>
                                  {step.description && (
                                    <p style={{ margin: '2px 0 0 0', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                      {step.description}
                                    </p>
                                  )}

                                  {/* Step Actions */}
                                  {step.actions && step.actions.length > 0 && (
                                    <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                      {step.actions.map((act) => (
                                        <div
                                          key={act.id}
                                          style={{
                                            fontSize: '0.72rem',
                                            padding: '4px 8px',
                                            background: 'var(--color-bg-primary)',
                                            borderRadius: 'var(--radius-md)',
                                            border: '1px solid var(--color-border-default)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            gap: '6px',
                                          }}
                                        >
                                          <span>
                                            🔧 <strong>{act.tool || act.type}</strong>: {act.description}
                                          </span>
                                          <span style={{ color: act.status === 'completed' ? 'var(--color-status-success)' : 'var(--color-status-danger)' }}>
                                            {act.status}
                                          </span>
                                        </div>
                                      ))}
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

      {/* Knowledge Base & Artifacts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {/* Knowledge Findings Card */}
        <div
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.1rem' }}>💡</span>
            <h4 style={{ margin: 0, fontSize: '0.925rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Strategic Findings & Insights
            </h4>
          </div>

          {plan.knowledge.findings.length === 0 ? (
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
              No findings recorded yet.
            </p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--color-text-primary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {plan.knowledge.findings.map((finding, idx) => (
                <li key={idx} style={{ lineHeight: 1.4 }}>{finding}</li>
              ))}
            </ul>
          )}

          {plan.knowledge.decisions.length > 0 && (
            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed var(--color-border-default)' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-accent-primary)', textTransform: 'uppercase' }}>
                Key Decisions
              </span>
              <ul style={{ margin: '4px 0 0 0', paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--color-text-primary)' }}>
                {plan.knowledge.decisions.map((dec, idx) => (
                  <li key={idx}>{dec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Registered Artifacts Card */}
        <div
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.1rem' }}>📦</span>
            <h4 style={{ margin: 0, fontSize: '0.925rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Registered Artifacts ({plan.artifacts.length})
            </h4>
          </div>

          {plan.artifacts.length === 0 ? (
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
              No output artifacts registered yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {plan.artifacts.map((art) => (
                <div
                  key={art.id}
                  style={{
                    padding: '8px 10px',
                    background: 'var(--color-bg-primary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-border-default)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      📄 {art.name}
                    </span>
                    <span className="field-value-display__chip" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>
                      {art.type}
                    </span>
                  </div>
                  {art.content_summary && (
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.76rem', color: 'var(--color-text-secondary)', lineHeight: 1.3 }}>
                      {art.content_summary}
                    </p>
                  )}
                  {art.path_or_uri && (
                    <code style={{ display: 'block', marginTop: '4px', fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                      {art.path_or_uri}
                    </code>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
