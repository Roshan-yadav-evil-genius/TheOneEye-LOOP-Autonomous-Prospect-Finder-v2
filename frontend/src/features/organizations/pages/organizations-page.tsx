import { Link } from 'react-router-dom'
import { useEffect } from 'react'

import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'
import { PageHeader } from '../../../shared/components/page-header'
import { useOrganizationsStore } from '../stores/organizations-store'

/**
 * Primary row click → organization page (Products tab by default).
 * Profile details and edit live on the Details tab.
 */
export function OrganizationsPage() {
  const { error, load, loading, organizations } = useOrganizationsStore()

  useEffect(() => {
    void load()
  }, [load])

  return (
    <>
      <PageHeader
        title="Organizations"
        subtitle="Open an organization to browse products, or use the Details tab for the profile."
        breadcrumbs={[{ label: 'Organizations' }]}
        actions={
          <Button asChild>
            <Link to="/orgs/new">New organization</Link>
          </Button>
        }
      />
      {error ? <p role="alert" className="error-banner">{error}</p> : null}
      {loading && organizations.length === 0 ? <p className="muted">Loading organizations…</p> : null}
      {!loading && organizations.length === 0 && !error ? (
        <EmptyState
          title="No organizations yet"
          body="Create an organization to start products and sales strategies."
          action={
            <Button asChild>
              <Link to="/orgs/new">New organization</Link>
            </Button>
          }
        />
      ) : (
        <EntityList>
          {organizations.map((organization) => (
            <EntityListItem
              key={organization.id}
              title={organization.name}
              to={`/orgs/${organization.id}`}
              editTo={`/orgs/${organization.id}?tab=details&mode=edit`}
              editLabel={`Edit ${organization.name}`}
              badge={organization.profile_validated ? 'validated' : 'incomplete'}
              badgeTone={organization.profile_validated ? 'success' : 'warning'}
              meta={organization.website}
              thumbnailUrl={organization.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${organization.thumbnail_url}` : '/static/org_placeholder.png'}
            />
          ))}
        </EntityList>
      )}
    </>
  )
}
