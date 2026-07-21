import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { UploadContext } from '../../forms/contexts/upload-context'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'
import { PageHeader } from '../../../shared/components/page-header'
import { useOrganizationsStore } from '../stores/organizations-store'
import { EntityEditModal } from '../../forms/components/entity-edit-modal'
import { organizationTemplate } from '../../forms/form-definitions'
import { organizationFormSections } from '../../forms/form-field-schema'
import { organizationFormThemes } from '../../forms/form-themes'
import { organizationsApi } from '../api/organizations-api'

function toWizardValue(organization: {
  name: string
  website: string
  primary_contact_email: string | null
  org_form: Record<string, unknown>
}) {
  return {
    identity: {
      name: organization.name,
      website: organization.website,
      primary_contact_email: organization.primary_contact_email ?? '',
      thumbnail_url: (organization as any).thumbnail_url,
    },
    ...organizationTemplate,
    ...organization.org_form,
  }
}

/**
 * Primary row click → organization page (Products tab by default).
 * Profile details and edit live on the Details tab.
 */
export function OrganizationsPage() {
  const { error, load, loading, organizations } = useOrganizationsStore()
  const [editingOrgId, setEditingOrgId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    void load()
  }, [load])

  const editingOrg = organizations.find((o) => o.id === editingOrgId)

  const handleSave = async (value: Record<string, unknown>) => {
    if (!editingOrgId) return
    setSubmitting(true)
    setSaveError(null)
    try {
      const { identity: identityValue, ...orgForm } = value
      const identity = identityValue as {
        name: string
        website: string
        primary_contact_email?: string
        thumbnail_url?: string
      }
      await organizationsApi.updateOrganizationProfile(editingOrgId, {
        form: orgForm,
        name: identity.name,
        website: identity.website,
        primary_contact_email: identity.primary_contact_email || null,
        thumbnail_url: identity.thumbnail_url || null,
      })
      setEditingOrgId(null)
      void load()
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save organization.')
    } finally {
      setSubmitting(false)
    }
  }

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
              onEdit={() => setEditingOrgId(organization.id)}
              editLabel={`Edit ${organization.name}`}
              badge={organization.profile_validated ? 'validated' : 'incomplete'}
              badgeTone={organization.profile_validated ? 'success' : 'warning'}
              meta={organization.website}
              thumbnailUrl={organization.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${organization.thumbnail_url}` : '/static/org_placeholder.png'}
            />
          ))}
        </EntityList>
      )}

      {editingOrg ? (
        <UploadContext.Provider value={`/api/v1/orgs/${editingOrgId}/thumbnail`}>
          <EntityEditModal
            open={!!editingOrgId}
            onOpenChange={(open) => !open && setEditingOrgId(null)}
            title="organization"
            sections={organizationFormSections}
            themes={organizationFormThemes}
            initialValue={toWizardValue(editingOrg as any)}
            submitting={submitting}
            serverError={saveError}
            onSubmit={handleSave}
          />
        </UploadContext.Provider>
      ) : null}
    </>
  )
}
