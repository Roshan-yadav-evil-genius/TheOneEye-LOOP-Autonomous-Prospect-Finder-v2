import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import {
  Badge,
  DataTable,
  FilterChips,
  SearchField,
} from '../../../shared/components/design-system'
import { Drawer } from '../../../shared/components/drawer'
import { ExpandablePanel } from '../../../shared/components/expandable-panel'
import { FormField } from '../../../shared/components/form-field'
import { shortId } from '../../../shared/lib/format'
import { WorkspaceShell } from '../components/workspace-shell'
import { useThreadsStore } from '../stores/threads-store'

export function ThreadsPage() {
  const { strategyId = '' } = useParams()
  const { load, open, snapshot, threads } = useThreadsStore()
  const [filter, setFilter] = useState<'all' | 'linked' | 'unlinked'>('all')
  const [query, setQuery] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)

  const visible = useMemo(() => {
    const q = query.toLowerCase()
    return threads.filter((thread) => {
      const linked = Boolean(thread.company_id || thread.sales_strategy_prospect_id)
      if (filter === 'linked' && !linked) return false
      if (filter === 'unlinked' && linked) return false
      if (!q) return true
      return `${thread.agent_role} ${thread.primary_thread_id} ${thread.status} ${thread.company_id ?? ''}`
        .toLowerCase()
        .includes(q)
    })
  }, [filter, query, threads])

  useEffect(() => {
    void load(strategyId)
  }, [load, strategyId])

  const inspect = async (threadId: string) => {
    await open(strategyId, threadId)
    setDrawerOpen(true)
  }

  return (
    <WorkspaceShell pageSubtitle="Agent thread runs for this strategy.">
      <div className="toolbar-row">
        <FilterChips
          label="Thread link filter"
          value={filter}
          onChange={(value) => setFilter(value as 'all' | 'linked' | 'unlinked')}
          options={[
            { value: 'all', label: 'All' },
            { value: 'linked', label: 'Linked' },
            { value: 'unlinked', label: 'Unlinked' },
          ]}
        />
        <SearchField value={query} onChange={setQuery} placeholder="Search threads" />
      </div>
      <DataTable
        headers={['Role', 'Thread', 'Status', 'Link', 'Actions']}
        empty={<p className="muted">No threads match this filter.</p>}
      >
        {visible.map((thread) => {
          const linked = Boolean(thread.company_id || thread.sales_strategy_prospect_id)
          return (
            <tr key={thread.id}>
              <td>{thread.agent_role}</td>
              <td>
                <strong>{shortId(thread.primary_thread_id, 12)}</strong>
                <small>{thread.primary_thread_id}</small>
              </td>
              <td>
                <Badge tone={thread.status === 'running' ? 'warning' : 'info'}>
                  {thread.status}
                </Badge>
              </td>
              <td>{linked ? 'Linked' : 'Unlinked'}</td>
              <td className="row-actions">
                <Button
                  variant="ghost"
                  onClick={() => void inspect(thread.primary_thread_id)}
                >
                  Inspect
                </Button>
              </td>
            </tr>
          )
        })}
      </DataTable>

      <Drawer
        open={drawerOpen && snapshot != null}
        onOpenChange={(open) => {
          setDrawerOpen(open)
        }}
        title={snapshot ? `Thread ${shortId(snapshot.thread_id, 12)}` : 'Thread'}
        description="Structured snapshot. Full state is under Advanced."
      >
        {snapshot ? (
          <div className="stack-gap">
            <FormField label="Sub-agent thread" help="Pick which agent thread snapshot to inspect.">
              <select
                className="control"
                value={snapshot.thread_id}
                onChange={(event) => void open(strategyId, event.target.value)}
              >
                {snapshot.available_threads.map((threadId) => (
                  <option key={threadId} value={threadId}>
                    {shortId(threadId, 16)}
                  </option>
                ))}
              </select>
            </FormField>
            <dl className="profile-summary__grid">
              <div className="profile-summary__field">
                <dt>Thread ID</dt>
                <dd>
                  <a href={`/api/v1/threads/${encodeURIComponent(snapshot.thread_id)}/chat/history`} target="_blank" rel="noreferrer" style={{ textDecoration: 'underline' }}>
                    {snapshot.thread_id}
                  </a>
                </dd>
              </div>
              <div className="profile-summary__field">
                <dt>Available threads</dt>
                <dd>{snapshot.available_threads.length}</dd>
              </div>
            </dl>
            <ExpandablePanel title="Advanced · raw state" defaultOpen={false}>
              <pre className="json-viewer">{JSON.stringify(snapshot.state, null, 2)}</pre>
            </ExpandablePanel>
          </div>
        ) : null}
      </Drawer>
    </WorkspaceShell>
  )
}
