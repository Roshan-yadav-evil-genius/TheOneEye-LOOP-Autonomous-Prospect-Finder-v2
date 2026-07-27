import { Link, useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { productTemplate } from '../../forms/form-definitions'
import { productFormSections } from '../../forms/form-field-schema'
import { productFormThemes } from '../../forms/form-themes'
import { organizationsApi } from '../../organizations/api/organizations-api'
import { Button } from '../../../shared/components/button'
import { IconLink, PlusIcon } from '../../../shared/components/icon-button'
import { PageHeader } from '../../../shared/components/page-header'
import { Tabs } from '../../../shared/components/tabs'
import { ProductStrategiesTab } from '../components/product-strategies-tab'
import { useProductDetailStore } from '../stores/product-detail-store'
import { toProductFormValue } from '../utils/icp-utils'

const DETAILS_TAB = 'details'
const STRATEGIES_TAB = 'strategies'

function toWizardValue(product: {
  name: string
  kind: string
  icp_form: Record<string, unknown>
}) {
  const { form_version: _formVersion, ..._formBody } = product.icp_form ?? {}
  return toProductFormValue(product)
}

function parseTab(value: string | null) {
  if (value === DETAILS_TAB) return DETAILS_TAB
  return STRATEGIES_TAB
}

export function ProductDetailPage() {
  const { orgId = '', productId = '' } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { error, load, loading, product, reset } = useProductDetailStore()
  const tab = parseTab(searchParams.get('tab'))
  const [parentOrg, setParentOrg] = useState<any>(null)

  useEffect(() => {
    reset()
    void load(productId)
    return () => reset()
  }, [load, productId, reset])

  useEffect(() => {
    let cancelled = false
    void organizationsApi
      .getOrganization(orgId)
      .then((organization) => {
        if (!cancelled) setParentOrg(organization)
      })
      .catch(() => {
        if (!cancelled) setParentOrg(null)
      })
    return () => {
      cancelled = true
    }
  }, [orgId])

  useEffect(() => {
    if (searchParams.get('mode') === 'edit') {
      navigate(`/orgs/${orgId}/products/${productId}/edit`, { replace: true })
    }
  }, [searchParams, navigate, orgId, productId])

  const setTab = (nextTab: string) => {
    const next = new URLSearchParams(searchParams)
    if (nextTab === STRATEGIES_TAB) {
      next.delete('tab')
    } else {
      next.set('tab', DETAILS_TAB)
    }
    setSearchParams(next, { replace: true })
  }

  return (
    <>
      <PageHeader
        title={product?.name ?? 'Product details'}
        subtitle="Full product profile and sales strategies for this offering."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { 
            label: parentOrg?.name ?? 'Organization', 
            to: `/orgs/${orgId}`,
            thumbnailUrl: parentOrg?.thumbnail_url,
            fallbackThumbnailUrl: '/static/org_placeholder.png'
          },
          { 
            label: product?.name ?? 'Product',
            thumbnailUrl: product ? (product as any).thumbnail_url : null,
            fallbackThumbnailUrl: '/static/product_service_placeholder.png'
          },
        ]}
        actions={
          <>
            <Button asChild variant="ghost">
              <Link to={`/orgs/${orgId}`}>← Organization</Link>
            </Button>
            {tab === STRATEGIES_TAB ? (
              <IconLink
                to={`/orgs/${orgId}/products/${productId}/sales-strategies/new`}
                label="Add sales strategy"
              >
                <PlusIcon />
              </IconLink>
            ) : (
              <Button asChild variant="ghost">
                <Link to={`/orgs/${orgId}/products/${productId}/edit`}>Edit</Link>
              </Button>
            )}
          </>
        }
      />
      {error && !product ? (
        <p role="alert" className="error-banner">
          {error}
        </p>
      ) : null}
      {loading || !product ? (
        !error ? <p className="muted">Loading product…</p> : null
      ) : (
        <>
          <Tabs
            label="Product sections"
            value={tab}
            onValueChange={setTab}
            items={[
              {
                value: STRATEGIES_TAB,
                label: 'Strategies',
                content: <ProductStrategiesTab />,
              },
              {
                value: DETAILS_TAB,
                label: 'Details',
                content: (
                  <FormProfileViewer
                    title="Product profile"
                    validated={product.profile_validated}
                    sections={productFormSections}
                    themes={productFormThemes}
                    value={toWizardValue(product)}
                    getEditUrl={(sectionKey) => `/orgs/${orgId}/products/${productId}/edit?step=${sectionKey}`}
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
