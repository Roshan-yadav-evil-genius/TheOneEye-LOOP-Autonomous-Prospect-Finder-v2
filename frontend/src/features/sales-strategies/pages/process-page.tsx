import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import {
  DataTable,
  ProcessControls,
  SideRail,
  WhiteboardPanel,
} from '../../../shared/components/design-system'
import { ExpandablePanel } from '../../../shared/components/expandable-panel'
import { KpiStrip } from '../../../shared/components/kpi-strip'
import { formatDateTime } from '../../../shared/lib/format'
import { salesStrategyApi } from '../api/sales-strategy-api'
import { WorkspaceShell } from '../components/workspace-shell'
import {
  useCompanyFinderProcessStore,
  useContactFinderProcessStore,
} from '../stores/process-store'
import {
  getCompanyFinderEfforts,
  getContactFinderEfforts,
  type AgentRunSummary,
} from '../api/efforts-api'

export function ProcessPage({ role }: { role: 'company-finder' | 'contact-finder' }) {
  const { orgId = '', strategyId = '' } = useParams()
  const companyStore = useCompanyFinderProcessStore()
  const contactStore = useContactFinderProcessStore()
  const { load, saveWhiteboard, start, status, stop, whiteboard } =
    role === 'company-finder' ? companyStore : contactStore
  const [view, setView] = useState<'control' | 'whiteboard' | 'efforts'>('control')
  const [content, setContent] = useState('')
  const [streamState, setStreamState] = useState<'idle' | 'live' | 'error'>('idle')
  const [efforts, setEfforts] = useState<AgentRunSummary[]>([])
  const [effortsLoading, setEffortsLoading] = useState(false)

  useEffect(() => {
    void load(strategyId, role)
    const timer = window.setInterval(() => {
      if (!document.hidden) void load(strategyId, role)
    }, 5000)
    return () => window.clearInterval(timer)
  }, [load, role, strategyId])

  useEffect(() => {
    const source = new EventSource(salesStrategyApi.processEventsUrl(strategyId, role))
    source.onopen = () => setStreamState('live')
    source.onerror = () => setStreamState('error')
    source.onmessage = () => {
      if (!document.hidden) void load(strategyId, role)
    }
    return () => source.close()
  }, [load, role, strategyId])

  useEffect(() => setContent(whiteboard?.content ?? ''), [whiteboard])

  const fetchEfforts = async () => {
    setEffortsLoading(true)
    try {
      if (role === 'company-finder') {
        const data = await getCompanyFinderEfforts(strategyId)
        setEfforts(data)
      } else {
        const data = await getContactFinderEfforts(strategyId)
        setEfforts(data)
      }
    } catch {
      setEfforts([])
    } finally {
      setEffortsLoading(false)
    }
  }

  useEffect(() => {
    if (view === 'efforts') {
      void fetchEfforts()
    }
  }, [role, strategyId, view])

  const handleViewChange = (next: 'control' | 'whiteboard' | 'efforts') => {
    setView(next)
  }

  const title = role === 'company-finder' ? 'Company finder' : 'Contact finder'

  return (
    <WorkspaceShell pageSubtitle={`${title} live status and controls.`}>
      <div className="subtabs subtabs--views" aria-label="Process views">
        <button
          type="button"
          className={view === 'control' ? 'active' : ''}
          onClick={() => handleViewChange('control')}
        >
          Control
        </button>
        <button
          type="button"
          className={view === 'whiteboard' ? 'active' : ''}
          onClick={() => handleViewChange('whiteboard')}
        >
          Whiteboard
        </button>
        <button
          type="button"
          className={view === 'efforts' ? 'active' : ''}
          onClick={() => handleViewChange('efforts')}
        >
          Efforts
        </button>
      </div>
      {view === 'control' ? (
        <>
          <KpiStrip
            items={[
              { label: 'Status', value: status?.actual_state ?? 'Loading' },
              { label: 'Executions', value: String(status?.execution_count ?? 0) },
              { label: 'Active company', value: status?.active_company_id ?? 'None' },
              { label: 'Event stream', value: streamState },
            ]}
          />
          <ProcessControls>
            {status?.actual_state === 'running' ? (
              <Button variant="danger" onClick={() => void stop(strategyId, role)}>
                Pause now
              </Button>
            ) : (
              <Button onClick={() => void start(strategyId, role)}>Start process</Button>
            )}
          </ProcessControls>
          <ExpandablePanel
            title="Event log"
            defaultOpen={false}
            summary={`${status?.logs.length ?? 0} events`}
          >
            <DataTable
              headers={['Time', 'Event', 'Message']}
              empty={<p className="muted">No events yet.</p>}
            >
              {(status?.logs ?? []).map((log) => (
                <tr key={log.id}>
                  <td>{formatDateTime(log.created_at)}</td>
                  <td>{log.event_code}</td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </DataTable>
          </ExpandablePanel>
        </>
      ) : view === 'whiteboard' ? (
        <div className="whiteboard-layout">
          <WhiteboardPanel
            content={content}
            onChange={setContent}
            onSave={() => void saveWhiteboard(strategyId, role, content)}
          />
          <SideRail title="Preview">
            <ReactMarkdown>{content}</ReactMarkdown>
          </SideRail>
        </div>
      ) : (
        /* Efforts Hierarchy view */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                {role === 'company-finder' ? 'Company Finder' : 'Contact Finder'} Efforts
              </h3>
              <p className="muted" style={{ margin: '4px 0 0 0', fontSize: '0.85rem' }}>
                Select an effort to view its dedicated sub-page, trimmed thread hierarchy, and live chat history.
              </p>
            </div>
            <Button variant="ghost" onClick={() => void fetchEfforts()} disabled={effortsLoading}>
              {effortsLoading ? 'Loading…' : '↺ Refresh'}
            </Button>
          </div>

          <DataTable
            headers={['Effort', 'Status', 'Child Threads', 'Created']}
            empty={
              effortsLoading ? (
                <p className="muted">Loading efforts…</p>
              ) : (
                <p className="muted">No {role} efforts recorded for this strategy yet.</p>
              )
            }
          >
            {efforts.map((effort) => {
              const seq = effort.contact_attempt_iteration ?? effort.attempt_iteration ?? 1
              const detailPath = `/orgs/${orgId}/sales-strategies/${strategyId}/${role}/effort/${seq}`
              const childCount = effort.child_thread_ids?.length || 0

              return (
                <tr key={effort.id}>
                  <td>
                    <Link
                      to={detailPath}
                      style={{
                        fontWeight: 700,
                        color: 'var(--color-accent-primary)',
                        textDecoration: 'none',
                        fontSize: '0.95rem',
                      }}
                    >
                      Effort #{seq}
                    </Link>
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background:
                          effort.status === 'completed'
                            ? 'rgba(34, 197, 94, 0.15)'
                            : effort.status === 'running'
                            ? 'rgba(59, 130, 246, 0.15)'
                            : 'rgba(239, 68, 68, 0.15)',
                        color:
                          effort.status === 'completed'
                            ? '#4ade80'
                            : effort.status === 'running'
                            ? '#60a5fa'
                            : '#f87171',
                        border: `1px solid ${
                          effort.status === 'completed'
                            ? 'rgba(34, 197, 94, 0.3)'
                            : effort.status === 'running'
                            ? 'rgba(59, 130, 246, 0.3)'
                            : 'rgba(239, 68, 68, 0.3)'
                        }`,
                        textTransform: 'uppercase',
                      }}
                    >
                      {effort.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem' }}>
                      {childCount + 1} {childCount + 1 === 1 ? 'thread' : 'threads'}
                    </span>
                  </td>
                  <td>{formatDateTime(effort.created_at)}</td>
                </tr>
              )
            })}
          </DataTable>
        </div>
      )}
    </WorkspaceShell>
  )
}


