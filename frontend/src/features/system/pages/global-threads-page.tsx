import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { DataTable } from '../../../shared/components/design-system'
import { PageHeader } from '../../../shared/components/page-header'
import { getGlobalThreads, deleteGlobalThread } from '../api/system-api'

export function GlobalThreadsPage() {
  const [data, setData] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  const fetchThreads = () => {
    setLoading(true)
    getGlobalThreads()
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to fetch global threads', err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchThreads()
  }, [])

  const handleDelete = async (threadId: string) => {
    if (window.confirm(`Delete thread: ${threadId}?`)) {
      try {
        await deleteGlobalThread(threadId)
        setData((prev) => prev.filter((t) => t !== threadId))
      } catch (err) {
        console.error('Failed to delete thread', err)
        alert('Failed to delete thread')
      }
    }
  }

  return (
    <div className="workspace-shell">
      <PageHeader
        title="Global Threads"
        subtitle="All agent run threads across the system."
      />
      <div style={{ padding: '0 2rem' }}>
        <DataTable
          headers={['Thread ID', 'Actions']}
          empty={loading ? <p className="muted">Loading threads...</p> : <p className="muted">No threads found.</p>}
        >
          {data.map((threadId) => (
            <tr key={threadId}>
              <td>
                <span style={{ fontFamily: 'monospace' }}>
                  <Link to={`/threads/${encodeURIComponent(threadId)}`} style={{ color: 'inherit', textDecoration: 'underline' }}>
                    {threadId}
                  </Link>
                </span>
              </td>
              <td style={{ textAlign: 'right' }}>
                <button
                  type="button"
                  onClick={() => handleDelete(threadId)}
                  title="Delete thread"
                  style={{
                    padding: '4px 10px',
                    background: 'rgba(239, 68, 68, 0.15)',
                    color: '#f87171',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  🗑️ Delete
                </button>
              </td>
            </tr>
          ))}
        </DataTable>
      </div>
    </div>
  )
}
