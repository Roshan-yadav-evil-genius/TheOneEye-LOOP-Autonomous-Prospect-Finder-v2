import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useEffect } from 'react'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { organizationTemplate } from '../../forms/form-definitions'
import { organizationFormSections } from '../../forms/form-field-schema'
import { organizationFormThemes } from '../../forms/form-themes'
import { IconLink, PlusIcon } from '../../../shared/components/icon-button'
import { Button } from '../../../shared/components/button'
import { PageHeader } from '../../../shared/components/page-header'
import { Tabs } from '../../../shared/components/tabs'
import { OrganizationProductsTab } from '../components/organization-products-tab'
import { useOrganizationDetailStore } from '../stores/organization-detail-store'

const PRODUCTS_TAB = 'products'
const DETAILS_TAB = 'details'

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

function parseTab(value: string | null) {
  if (value === DETAILS_TAB) return DETAILS_TAB
  return PRODUCTS_TAB
}

export function OrganizationDetailPage() {
  const { orgId = '' } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { error, load, loading, organization, reset } = useOrganizationDetailStore()
  const tab = parseTab(searchParams.get('tab'))

  useEffect(() => {
    reset()
    void load(orgId)
    return () => reset()
  }, [load, orgId, reset])

  // Redirect to edit page if edit mode requested
  useEffect(() => {
    if (searchParams.get('mode') === 'edit') {
      navigate(`/orgs/${orgId}/edit`, { replace: true })
    }
  }, [searchParams, navigate, orgId])

  const setTab = (nextTab: string) => {
    const next = new URLSearchParams(searchParams)
    if (nextTab === PRODUCTS_TAB) {
      next.delete('tab')
    } else {
      next.set('tab', DETAILS_TAB)
    }
    setSearchParams(next, { replace: true })
  }

  return (
    <>
      <PageHeader
        title={organization?.name ?? 'Organization'}
        subtitle="Products and services for this organization, with profile details on the last tab."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { 
            label: organization?.name ?? 'Organization',
            thumbnailUrl: organization ? (organization as any).thumbnail_url : null,
            fallbackThumbnailUrl: '/static/org_placeholder.png'
          },
        ]}
        actions={
          <>
            {tab === PRODUCTS_TAB ? (
              <IconLink to={`/orgs/${orgId}/products/new`} label="Add product">
                <PlusIcon />
              </IconLink>
            ) : (
              <Button asChild variant="ghost">
                <Link to={`/orgs/${orgId}/edit`}>Edit</Link>
              </Button>
            )}
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
        <>
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
                value: DETAILS_TAB,
                label: 'Details',
                content: (
                  <FormProfileViewer
                    title="Organization profile"
                    validated={organization.profile_validated}
                    sections={organizationFormSections}
                    themes={organizationFormThemes}
                    value={toWizardValue(organization)}
                  />
                ),
              },
            ]}
          />
        </>
      )}
    </>
  )
}
