import { Link } from 'react-router-dom'
import { useEffect } from 'react'

import { Button } from '../../../shared/components/button'
import { Badge, DataTable, EmptyState } from '../../../shared/components/design-system'
import { KpiStrip } from '../../../shared/components/kpi-strip'
import { PageHeader } from '../../../shared/components/page-header'
import { useOperatorHomeStore } from '../stores/operator-home-store'

export function OperatorHomePage() {
  const {
    activeJobs,
    build,
    dlqCount,
    error,
    health,
    incompleteProfiles,
    load,
    loading,
    organizations,
    runningFinders,
  } = useOperatorHomeStore()

  useEffect(() => {
    void load()
  }, [load])

  return (
    <>
      <PageHeader
        title="LOOP operator home"
        subtitle="Recent organizations, incomplete profiles, running finders, and runtime health."
        breadcrumbs={[{ label: 'Home' }]}
        actions={
          <>
            <Button asChild variant="ghost">
              <Link to="/orgs">Organizations</Link>
            </Button>
            <Button asChild variant="ghost">
              <Link to="/admin">Admin</Link>
            </Button>
            <Button onClick={() => void load()} disabled={loading}>
              {loading ? 'Refreshing…' : 'Refresh'}
            </Button>
          </>
        }
      />

      <KpiStrip
        label="Operator overview"
        items={[
          {
            label: 'API',
            value: health?.status === 'ok' ? 'Live' : 'Offline',
          },
          { label: 'Active jobs', value: String(activeJobs) },
          { label: 'Pending DLQ', value: String(dlqCount) },
          { label: 'Running finders', value: String(runningFinders.length) },
          { label: 'Build', value: build?.version ?? 'Unknown' },
        ]}
      />

      {error ? <p role="alert" className="error-banner">{error}</p> : null}

      <div className="home-grid">
        <section className="home-panel">
          <div className="home-panel__header">
            <h2>Recent organizations</h2>
            <Button asChild variant="ghost">
              <Link to="/orgs">View all</Link>
            </Button>
          </div>
          {organizations.length === 0 ? (
            <EmptyState
              title="No organizations yet"
              body="Create an organization to begin operator work."
              action={
                <Button asChild>
                  <Link to="/orgs/new">New organization</Link>
                </Button>
              }
            />
          ) : (
            <DataTable headers={['Organization', 'Website', 'Status']}>
              {organizations.map((org) => (
                <tr key={org.id}>
                  <td>
                    <Link to={`/orgs/${org.id}`}>
                      <strong>{org.name}</strong>
                    </Link>
                  </td>
                  <td>{org.website}</td>
                  <td>
                    <Badge tone={org.profile_validated ? 'success' : 'warning'}>
                      {org.profile_validated ? 'validated' : 'incomplete'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </DataTable>
          )}
        </section>

        <section className="home-panel">
          <div className="home-panel__header">
            <h2>Incomplete profiles</h2>
          </div>
          {incompleteProfiles.length === 0 ? (
            <p className="muted">All recent organizations are validated.</p>
          ) : (
            <DataTable headers={['Organization', 'Next action']}>
              {incompleteProfiles.map((org) => (
                <tr key={org.id}>
                  <td>
                    <Link to={`/orgs/${org.id}`}>
                      <strong>{org.name}</strong>
                    </Link>
                  </td>
                  <td>
                    <Button asChild variant="ghost">
                      <Link to={`/orgs/${org.id}`}>Complete profile</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </DataTable>
          )}
        </section>

        <section className="home-panel home-panel--wide">
          <div className="home-panel__header">
            <h2>Running finders</h2>
            {dlqCount > 0 ? (
              <Button asChild variant="ghost">
                <Link to="/admin">DLQ ({dlqCount})</Link>
              </Button>
            ) : null}
          </div>
          <DataTable
            headers={['Strategy', 'Organization', 'Role', 'State', 'Open']}
            empty={<p className="muted">No sampled finders are running right now.</p>}
          >
            {runningFinders.map((finder) => (
              <tr key={`${finder.strategyId}-${finder.role}`}>
                <td>
                  <strong>{finder.strategyName}</strong>
                </td>
                <td>{finder.orgName}</td>
                <td>{finder.role}</td>
                <td>
                  <Badge tone="warning">{finder.state}</Badge>
                </td>
                <td>
                  <Button asChild variant="ghost">
                    <Link
                      to={`/orgs/${finder.orgId}/sales-strategies/${finder.strategyId}/${finder.role}`}
                    >
                      Open
                    </Link>
                  </Button>
                </td>
              </tr>
            ))}
          </DataTable>
        </section>
      </div>
    </>
  )
}
