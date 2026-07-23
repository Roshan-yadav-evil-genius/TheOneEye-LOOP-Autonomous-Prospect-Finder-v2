import { Link, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'
import { PageHeader } from '../../../shared/components/page-header'
import { useOrganizationsStore } from '../stores/organizations-store'
import { organizationsApi } from '../api/organizations-api'

export function OrganizationsPage() {
  const { error, load, loading, organizations } = useOrganizationsStore()
  const navigate = useNavigate()
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    void load()
  }, [load])

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return
    setDeleteError(null)
    try {
      await organizationsApi.deleteOrganization(id)
      void load()
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete organization.')
    }
  }

  return (
    <>
      <PageHeader
        title="Organizations"
        subtitle="Open an organization to browse products, or edit details in split-panel mode."
        breadcrumbs={[{ label: 'Organizations' }]}
        actions={
          <Button asChild>
            <Link to="/orgs/new">New organization</Link>
          </Button>
        }
      />
      {error ? <p role="alert" className="error-banner">{error}</p> : null}
      {deleteError ? <p role="alert" className="error-banner">{deleteError}</p> : null}
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
          {organizations.map((organization) => {
            const hasNoChildren = (organization.products_count ?? 0) === 0
            return (
              <EntityListItem
                key={organization.id}
                title={organization.name}
                to={`/orgs/${organization.id}`}
                onEdit={() => navigate(`/orgs/${organization.id}/edit`)}
                editLabel={`Edit ${organization.name}`}
                onDelete={hasNoChildren ? () => handleDelete(organization.id, organization.name) : undefined}
                deleteLabel={`Delete ${organization.name}`}
                badge={organization.profile_validated ? 'validated' : 'incomplete'}
                badgeTone={organization.profile_validated ? 'success' : 'warning'}
                meta={organization.website}
                thumbnailUrl={organization.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${organization.thumbnail_url}` : '/static/org_placeholder.png'}
              />
            )
          })}
        </EntityList>
      )}
    </>
  )
}
