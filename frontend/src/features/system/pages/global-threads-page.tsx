import { useEffect, useState } from 'react'

import { DataTable } from '../../../shared/components/design-system'
import { PageHeader } from '../../../shared/components/page-header'
import { getGlobalThreads } from '../api/system-api'

export function GlobalThreadsPage() {
  const [data, setData] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    getGlobalThreads()
      .then((res) => {
        if (mounted) {
          setData(res)
          setLoading(false)
        }
      })
      .catch((err) => {
        console.error('Failed to fetch global threads', err)
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="workspace-shell">
      <PageHeader
        title="Global Threads"
        subtitle="All agent run threads across the system."
      />
      <div style={{ padding: '0 2rem' }}>
        <DataTable
          headers={['Thread ID']}
          empty={loading ? <p className="muted">Loading threads...</p> : <p className="muted">No threads found.</p>}
        >
          {data.map((threadId) => (
            <tr key={threadId}>
              <td>
                <span style={{ fontFamily: 'monospace' }}>{threadId}</span>
              </td>
            </tr>
          ))}
        </DataTable>
      </div>
    </div>
  )
}
