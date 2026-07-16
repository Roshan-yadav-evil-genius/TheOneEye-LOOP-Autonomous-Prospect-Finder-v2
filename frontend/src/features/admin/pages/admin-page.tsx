import { useEffect, useMemo, useState } from 'react'

import type { AuditEvent, DeadLetter, JobRun } from '../api/admin-api'
import { Button } from '../../../shared/components/button'
import {
  Badge,
  DataTable,
  FilterChips,
  SearchField,
} from '../../../shared/components/design-system'
import { Drawer } from '../../../shared/components/drawer'
import { ExpandablePanel } from '../../../shared/components/expandable-panel'
import { KpiStrip } from '../../../shared/components/kpi-strip'
import { PageHeader } from '../../../shared/components/page-header'
import { formatDateTime, shortId } from '../../../shared/lib/format'
import { useAdminStore } from '../stores/admin-store'

type AdminTab = 'jobs' | 'dlq' | 'audit'

export function AdminPage() {
  const store = useAdminStore()
  const load = store.load
  const [tab, setTab] = useState<AdminTab>('jobs')
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedJob, setSelectedJob] = useState<JobRun | null>(null)
  const [selectedDlq, setSelectedDlq] = useState<DeadLetter | null>(null)
  const [selectedAudit, setSelectedAudit] = useState<AuditEvent | null>(null)

  useEffect(() => {
    void load()
  }, [load])

  const activeJobs = store.jobs.filter((job) => !['completed', 'cancelled'].includes(job.status))
  const pendingDlq = store.deadLetters.filter((item) => item.replay_state === 'pending')

  const jobStatuses = useMemo(() => {
    const statuses = new Set(store.jobs.map((job) => job.status))
    return ['all', ...Array.from(statuses).sort()]
  }, [store.jobs])

  const filteredJobs = useMemo(() => {
    const q = query.toLowerCase()
    return store.jobs.filter((job) => {
      if (statusFilter !== 'all' && job.status !== statusFilter) return false
      if (!q) return true
      return `${job.task_key} ${job.status} ${job.id} ${job.error ?? ''}`
        .toLowerCase()
        .includes(q)
    })
  }, [query, statusFilter, store.jobs])

  const filteredDlq = useMemo(() => {
    const q = query.toLowerCase()
    return store.deadLetters.filter((item) => {
      if (!q) return true
      return `${item.queue} ${item.reason} ${item.replay_state} ${item.id}`
        .toLowerCase()
        .includes(q)
    })
  }, [query, store.deadLetters])

  const filteredAudit = useMemo(() => {
    const q = query.toLowerCase()
    return store.audit.filter((event) => {
      if (!q) return true
      return `${event.action} ${event.actor} ${event.entity_type} ${event.entity_id}`
        .toLowerCase()
        .includes(q)
    })
  }, [query, store.audit])

  return (
    <>
      <PageHeader
        title="Runtime administration"
        subtitle="Jobs and dead-letter queue first. Audit is available as a secondary tab."
        breadcrumbs={[{ label: 'Admin' }]}
        actions={<Button onClick={() => void store.load()}>Refresh</Button>}
      />
      {store.error ? <p role="alert" className="error-banner">{store.error}</p> : null}
      <KpiStrip
        items={[
          { label: 'Active jobs', value: String(activeJobs.length) },
          { label: 'Pending DLQ', value: String(pendingDlq.length) },
          { label: 'Schedules', value: String(store.schedules.length) },
          { label: 'Audit events', value: String(store.audit.length) },
        ]}
      />

      <div className="toolbar-row">
        <nav className="workspace-tabs" aria-label="Admin sections">
          {(
            [
              ['jobs', 'Jobs'],
              ['dlq', 'Dead letters'],
              ['audit', 'Audit'],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={tab === value ? 'workspace-tab active' : 'workspace-tab'}
              onClick={() => {
                setTab(value)
                setQuery('')
                setStatusFilter('all')
              }}
            >
              {label}
            </button>
          ))}
        </nav>
        <SearchField
          value={query}
          onChange={setQuery}
          placeholder={
            tab === 'jobs'
              ? 'Search jobs'
              : tab === 'dlq'
                ? 'Search dead letters'
                : 'Search audit'
          }
        />
      </div>

      {tab === 'jobs' ? (
        <>
          <FilterChips
            label="Job status filter"
            value={statusFilter}
            onChange={setStatusFilter}
            options={jobStatuses.map((status) => ({
              value: status,
              label: status === 'all' ? 'All statuses' : status,
            }))}
          />
          <DataTable
            headers={['Status', 'Type', 'Created', 'Attempts', 'Error', 'Actions']}
            empty={<p className="muted">No jobs match this filter.</p>}
          >
            {filteredJobs.map((job) => (
              <tr
                key={job.id}
                className="data-table__row--clickable"
                onClick={() => setSelectedJob(job)}
              >
                <td>
                  <Badge
                    tone={
                      job.status === 'completed'
                        ? 'success'
                        : job.status === 'failed'
                          ? 'danger'
                          : 'warning'
                    }
                  >
                    {job.status}
                  </Badge>
                </td>
                <td>
                  <strong>{job.task_key}</strong>
                  <small>{shortId(job.id)}</small>
                </td>
                <td>{formatDateTime(job.created_at)}</td>
                <td>{job.attempts}</td>
                <td>{job.error ? shortId(job.error, 40) : '—'}</td>
                <td className="row-actions">
                  <Button
                    variant="ghost"
                    onClick={(event) => {
                      event.stopPropagation()
                      setSelectedJob(job)
                    }}
                  >
                    Details
                  </Button>
                </td>
              </tr>
            ))}
          </DataTable>
        </>
      ) : null}

      {tab === 'dlq' ? (
        <DataTable
          headers={['Queue', 'Reason', 'Attempts', 'State', 'Created', 'Actions']}
          empty={<p className="muted">No dead letters.</p>}
        >
          {filteredDlq.map((item) => (
            <tr
              key={item.id}
              className="data-table__row--clickable"
              onClick={() => setSelectedDlq(item)}
            >
              <td>{item.queue}</td>
              <td>{item.reason}</td>
              <td>{item.attempts}</td>
              <td>
                <Badge tone={item.replay_state === 'pending' ? 'warning' : 'info'}>
                  {item.replay_state}
                </Badge>
              </td>
              <td>{formatDateTime(item.created_at)}</td>
              <td className="row-actions">
                <Button
                  disabled={item.replay_state !== 'pending'}
                  onClick={(event) => {
                    event.stopPropagation()
                    void store.replay(item.id)
                  }}
                >
                  Replay
                </Button>
                <Button
                  variant="danger"
                  disabled={item.replay_state !== 'pending'}
                  onClick={(event) => {
                    event.stopPropagation()
                    void store.discard(item.id)
                  }}
                >
                  Discard
                </Button>
              </td>
            </tr>
          ))}
        </DataTable>
      ) : null}

      {tab === 'audit' ? (
        <DataTable
          headers={['When', 'Actor', 'Action', 'Entity', 'Reason', 'Actions']}
          empty={<p className="muted">No audit events.</p>}
        >
          {filteredAudit.map((event) => (
            <tr
              key={event.id}
              className="data-table__row--clickable"
              onClick={() => setSelectedAudit(event)}
            >
              <td>{formatDateTime(event.created_at)}</td>
              <td>{event.actor}</td>
              <td>{event.action}</td>
              <td>
                {event.entity_type}
                <small>{shortId(event.entity_id)}</small>
              </td>
              <td>{event.reason ?? '—'}</td>
              <td className="row-actions">
                <Button
                  variant="ghost"
                  onClick={(event_) => {
                    event_.stopPropagation()
                    setSelectedAudit(event)
                  }}
                >
                  Details
                </Button>
              </td>
            </tr>
          ))}
        </DataTable>
      ) : null}

      <Drawer
        open={selectedJob != null}
        onOpenChange={(open) => {
          if (!open) setSelectedJob(null)
        }}
        title={selectedJob ? selectedJob.task_key : 'Job'}
        description={selectedJob ? `Status ${selectedJob.status}` : undefined}
      >
        {selectedJob ? (
          <div className="stack-gap">
            <dl className="profile-summary__grid">
              <div className="profile-summary__field">
                <dt>ID</dt>
                <dd>{selectedJob.id}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Created</dt>
                <dd>{formatDateTime(selectedJob.created_at)}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Attempts</dt>
                <dd>{selectedJob.attempts}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Error</dt>
                <dd>{selectedJob.error ?? '—'}</dd>
              </div>
            </dl>
            <ExpandablePanel title="Advanced · payload" defaultOpen={false}>
              <pre className="json-viewer">{JSON.stringify(selectedJob.payload, null, 2)}</pre>
            </ExpandablePanel>
          </div>
        ) : null}
      </Drawer>

      <Drawer
        open={selectedDlq != null}
        onOpenChange={(open) => {
          if (!open) setSelectedDlq(null)
        }}
        title={selectedDlq ? selectedDlq.queue : 'Dead letter'}
        description={selectedDlq?.reason}
      >
        {selectedDlq ? (
          <div className="stack-gap">
            <dl className="profile-summary__grid">
              <div className="profile-summary__field">
                <dt>Job run</dt>
                <dd>{selectedDlq.job_run_id}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>State</dt>
                <dd>{selectedDlq.replay_state}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Attempts</dt>
                <dd>{selectedDlq.attempts}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Created</dt>
                <dd>{formatDateTime(selectedDlq.created_at)}</dd>
              </div>
            </dl>
            <ExpandablePanel title="Advanced · payload" defaultOpen>
              <pre className="json-viewer">{JSON.stringify(selectedDlq.payload, null, 2)}</pre>
            </ExpandablePanel>
          </div>
        ) : null}
      </Drawer>

      <Drawer
        open={selectedAudit != null}
        onOpenChange={(open) => {
          if (!open) setSelectedAudit(null)
        }}
        title={selectedAudit ? selectedAudit.action : 'Audit event'}
        description={selectedAudit ? `${selectedAudit.actor} · ${selectedAudit.entity_type}` : undefined}
      >
        {selectedAudit ? (
          <div className="stack-gap">
            <dl className="profile-summary__grid">
              <div className="profile-summary__field">
                <dt>When</dt>
                <dd>{formatDateTime(selectedAudit.created_at)}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Entity</dt>
                <dd>
                  {selectedAudit.entity_type} / {selectedAudit.entity_id}
                </dd>
              </div>
              <div className="profile-summary__field">
                <dt>Reason</dt>
                <dd>{selectedAudit.reason ?? '—'}</dd>
              </div>
              <div className="profile-summary__field">
                <dt>Request</dt>
                <dd>{selectedAudit.request_id ?? '—'}</dd>
              </div>
            </dl>
            <ExpandablePanel title="Advanced · before / after" defaultOpen>
              <pre className="json-viewer">
                {JSON.stringify(
                  { before: selectedAudit.before, after: selectedAudit.after },
                  null,
                  2,
                )}
              </pre>
            </ExpandablePanel>
          </div>
        ) : null}
      </Drawer>
    </>
  )
}
