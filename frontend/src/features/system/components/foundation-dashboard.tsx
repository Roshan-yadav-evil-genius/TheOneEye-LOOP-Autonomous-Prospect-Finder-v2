import { Link } from 'react-router-dom'
import { useEffect } from 'react'

import { Button } from '../../../shared/components/button'
import { Card } from '../../../shared/components/card'
import { MetricTile } from '../../../shared/components/metric-tile'
import { PageHeader } from '../../../shared/components/page-header'
import { useSystemStatusStore } from '../stores/system-status-store'

export function FoundationDashboard() {
  const { build, error, health, isLoading, load } = useSystemStatusStore()

  useEffect(() => {
    void load()
  }, [load])

  return (
    <>
      <PageHeader
        title="LOOP operator foundation"
        subtitle="Greenfield API and web shells aligned to the production modular-monolith plan."
        actions={
          <>
            <Button asChild variant="ghost">
              <Link to="/orgs">Organizations</Link>
            </Button>
            <Button onClick={() => void load()} disabled={isLoading}>
              {isLoading ? 'Checking…' : 'Check API'}
            </Button>
          </>
        }
      />

      <div className="metric-grid" aria-label="Foundation status">
        <MetricTile label="Web shell" value="Ready" />
        <MetricTile label="API" value={health?.status === 'ok' ? 'Live' : 'Offline'} />
        <MetricTile label="Build" value={build?.version ?? 'Unknown'} />
      </div>

      <Card title="Stage 0 capabilities">
        {error ? <p role="alert">{error}</p> : null}
        <ul className="foundation-list">
          <li>
            <span>Typed OpenAPI contract</span>
            <strong className="status status--ok">Generated</strong>
          </li>
          <li>
            <span>Axios boundary modules</span>
            <strong className="status status--ok">Configured</strong>
          </li>
          <li>
            <span>Domain-scoped Zustand state</span>
            <strong className="status status--ok">Configured</strong>
          </li>
          <li>
            <span>PostgreSQL and Redis readiness</span>
            <strong className="status">Dependency setup</strong>
          </li>
        </ul>
      </Card>
    </>
  )
}
