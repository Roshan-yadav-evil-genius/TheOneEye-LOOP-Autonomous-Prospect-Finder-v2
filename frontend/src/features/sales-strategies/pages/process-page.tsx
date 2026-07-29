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
import { apiClient } from '../../../shared/api/client'
import { salesStrategyApi } from '../api/sales-strategy-api'
import { WorkspaceShell } from '../components/workspace-shell'
import {
  useCompanyFinderProcessStore,
  useContactFinderProcessStore,
} from '../stores/process-store'

export function ProcessPage({ role }: { role: 'company-finder' | 'contact-finder' }) {
  const { strategyId = '' } = useParams()
  const companyStore = useCompanyFinderProcessStore()
  const contactStore = useContactFinderProcessStore()
  const { load, saveWhiteboard, start, status, stop, whiteboard } =
    role === 'company-finder' ? companyStore : contactStore
  const [view, setView] = useState<'control' | 'whiteboard' | 'threads'>('control')
  const [content, setContent] = useState('')
  const [streamState, setStreamState] = useState<'idle' | 'live' | 'error'>('idle')
  const [agentThreads, setAgentThreads] = useState<string[]>([])
  const [threadsLoading, setThreadsLoading] = useState(false)

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

  const fetchAgentThreads = async () => {
    setThreadsLoading(true)
    try {
      const apiRole = role === 'company-finder' ? 'company-finder' : 'contact-finder'
      const res = await apiClient.get<string[]>(
        `/api/v1/sales-strategies/${strategyId}/agents/${apiRole}/threads`
      )
      setAgentThreads(res.data)
    } catch {
      setAgentThreads([])
    } finally {
      setThreadsLoading(false)
    }
  }

  useEffect(() => {
    if (view === 'threads') {
      void fetchAgentThreads()
    }
  }, [role, strategyId, view])

  const handleViewChange = (next: 'control' | 'whiteboard' | 'threads') => {
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
          className={view === 'threads' ? 'active' : ''}
          onClick={() => handleViewChange('threads')}
        >
          Threads
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
        /* Threads view */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p className="muted" style={{ margin: 0, fontSize: '0.875rem' }}>
              {role === 'company-finder' ? 'Company Finder' : 'Contact Finder'} agent threads for this strategy.
            </p>
            <Button variant="ghost" onClick={() => void fetchAgentThreads()} disabled={threadsLoading}>
              {threadsLoading ? 'Loading…' : '↺ Refresh'}
            </Button>
          </div>
          <DataTable
            headers={['Thread ID', 'Actions']}
            empty={
              threadsLoading
                ? <p className="muted">Loading threads…</p>
                : <p className="muted">No {role} threads found for this strategy.</p>
            }
          >
            {agentThreads.map((threadId) => (
              <tr key={threadId}>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', wordBreak: 'break-all' }}>
                    {threadId}
                  </span>
                </td>
                <td className="row-actions">
                  <Link
                    to={`/threads/${encodeURIComponent(threadId)}`}
                    style={{ textDecoration: 'underline', fontSize: '0.85rem' }}
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>
        </div>
      )}
    </WorkspaceShell>
  )
}

