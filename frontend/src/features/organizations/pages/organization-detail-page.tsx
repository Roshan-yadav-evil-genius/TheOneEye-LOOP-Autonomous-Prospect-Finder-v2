import { useParams, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { SectionWizard } from '../../forms/components/section-wizard'
import { organizationTemplate } from '../../forms/form-definitions'
import { organizationFormSections } from '../../forms/form-field-schema'
import { organizationFormThemes } from '../../forms/form-themes'
import { IconLink, PlusIcon } from '../../../shared/components/icon-button'
import { Button } from '../../../shared/components/button'
import { PageHeader } from '../../../shared/components/page-header'
import { Tabs } from '../../../shared/components/tabs'
import { OrganizationProductsTab } from '../components/organization-products-tab'
import { OrganizationChatTab } from '../components/organization-chat-tab'
import { useOrganizationDetailStore } from '../stores/organization-detail-store'
import { useOrganizationChatStore } from '../stores/organization-chat-store'

const PRODUCTS_TAB = 'products'
const DETAILS_TAB = 'details'
const CHAT_TAB = 'chat'

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
    },
    ...organizationTemplate,
    ...organization.org_form,
  }
}

function parseTab(value: string | null, mode: string | null) {
  if (value === DETAILS_TAB || mode === 'edit') return DETAILS_TAB
  if (value === CHAT_TAB) return CHAT_TAB
  return PRODUCTS_TAB
}

/**
 * Primary click from org list lands here on the Products tab.
 * Edit is opened from the list edit icon via `?tab=details&mode=edit`.
 */
export function OrganizationDetailPage() {
  const { orgId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const { error, load, loading, organization, reset, save, saved, submitting } =
    useOrganizationDetailStore()
  const tab = parseTab(searchParams.get('tab'), searchParams.get('mode'))
  const [mode, setMode] = useState<'view' | 'edit'>(
    searchParams.get('mode') === 'edit' ? 'edit' : 'view',
  )

  useEffect(() => {
    reset()
    void load(orgId)
    return () => reset()
  }, [load, orgId, reset])

  useEffect(() => {
    setMode(searchParams.get('mode') === 'edit' ? 'edit' : 'view')
  }, [orgId, searchParams])

  useEffect(() => {
    if (searchParams.get('mode') !== 'edit' || searchParams.get('tab') === DETAILS_TAB) return
    const next = new URLSearchParams(searchParams)
    next.set('tab', DETAILS_TAB)
    setSearchParams(next, { replace: true })
  }, [orgId, searchParams, setSearchParams])

  useEffect(() => {
    if (!saved) return
    setMode('view')
    const next = new URLSearchParams(searchParams)
    next.delete('mode')
    next.set('tab', DETAILS_TAB)
    setSearchParams(next, { replace: true })
  }, [saved, searchParams, setSearchParams])

  const setTab = (nextTab: string) => {
    const next = new URLSearchParams(searchParams)
    if (nextTab === PRODUCTS_TAB) {
      next.delete('tab')
      next.delete('mode')
      setMode('view')
    } else if (nextTab === CHAT_TAB) {
      next.set('tab', CHAT_TAB)
      next.delete('mode')
      setMode('view')
    } else {
      next.set('tab', DETAILS_TAB)
      next.delete('mode')
      setMode('view')
      
      if (useOrganizationChatStore.getState().profileDirtyFromChat) {
        useOrganizationChatStore.getState().clearDirtyFlag()
        void load(orgId)
      }
    }
    setSearchParams(next, { replace: true })
  }

  const cancelEdit = () => {
    setMode('view')
    const next = new URLSearchParams(searchParams)
    next.delete('mode')
    setSearchParams(next, { replace: true })
  }

  return (
    <>
      <PageHeader
        title={organization?.name ?? 'Organization'}
        subtitle="Products and services for this organization, with profile details on the last tab."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { label: organization?.name ?? 'Organization' },
        ]}
        actions={
          <>
            {tab === PRODUCTS_TAB ? (
              <IconLink to={`/orgs/${orgId}/products/new`} label="Add product">
                <PlusIcon />
              </IconLink>
            ) : mode === 'edit' ? (
              <Button type="button" variant="ghost" onClick={cancelEdit}>
                Cancel edit
              </Button>
            ) : null}
          </>
        }
      />
      {error && !organization ? (
        <p role="alert" className="error-banner">
          {error}
        </p>
      ) : null}
      {loading || !organization ? (
        !error ? <p className="muted">Loading organization…</p> : null
      ) : (
        <Tabs
          label="Organization sections"
          value={tab}
          onValueChange={setTab}
          items={[
            {
              value: PRODUCTS_TAB,
              label: 'Products',
              content: <OrganizationProductsTab />,
            },
            {
              value: CHAT_TAB,
              label: 'Chat',
              content: <OrganizationChatTab />,
            },
            {
              value: DETAILS_TAB,
              label: 'Details',
              content:
                mode === 'view' ? (
                  <FormProfileViewer
                    title="Organization profile"
                    validated={organization.profile_validated}
                    sections={organizationFormSections}
                    themes={organizationFormThemes}
                    value={toWizardValue(organization)}
                  />
                ) : (
                  <SectionWizard
                    key={`${organization.id}-edit-${organization.profile_validated}`}
                    title="organization"
                    sections={organizationFormSections}
                    themes={organizationFormThemes}
                    initialValue={toWizardValue(organization)}
                    submitLabel="Save organization"
                    submitting={submitting}
                    serverError={error}
                    onSubmit={(value) => save(orgId, value)}
                  />
                ),
            },
          ]}
        />
      )}
    </>
  )
}
