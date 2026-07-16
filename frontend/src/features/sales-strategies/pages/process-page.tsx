import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { useParams } from 'react-router-dom'

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

export function ProcessPage({ role }: { role: 'company-finder' | 'contact-finder' }) {
  const { strategyId = '' } = useParams()
  const companyStore = useCompanyFinderProcessStore()
  const contactStore = useContactFinderProcessStore()
  const { load, saveWhiteboard, start, status, stop, whiteboard } =
    role === 'company-finder' ? companyStore : contactStore
  const [view, setView] = useState<'control' | 'whiteboard'>('control')
  const [content, setContent] = useState('')
  const [streamState, setStreamState] = useState<'idle' | 'live' | 'error'>('idle')

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

  const title = role === 'company-finder' ? 'Company finder' : 'Contact finder'

  return (
    <WorkspaceShell pageSubtitle={`${title} live status and controls.`}>
      <div className="subtabs subtabs--views" aria-label="Process views">
        <button
          type="button"
          className={view === 'control' ? 'active' : ''}
          onClick={() => setView('control')}
        >
          Control
        </button>
        <button
          type="button"
          className={view === 'whiteboard' ? 'active' : ''}
          onClick={() => setView('whiteboard')}
        >
          Whiteboard
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
      ) : (
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
      )}
    </WorkspaceShell>
  )
}
