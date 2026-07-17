import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { EntityEditModal } from '../../forms/components/entity-edit-modal'
import { productTemplate } from '../../forms/form-definitions'
import { productFormSections } from '../../forms/form-field-schema'
import { productFormThemes } from '../../forms/form-themes'
import { organizationsApi } from '../../organizations/api/organizations-api'
import { Button } from '../../../shared/components/button'
import { IconLink, PlusIcon } from '../../../shared/components/icon-button'
import { PageHeader } from '../../../shared/components/page-header'
import { Tabs } from '../../../shared/components/tabs'
import { ProductStrategiesTab } from '../components/product-strategies-tab'
import { ProductChatTab } from '../components/product-chat-tab'
import { useProductDetailStore } from '../stores/product-detail-store'
import { useProductChatStore } from '../stores/product-chat-store'

const DETAILS_TAB = 'details'
const CHAT_TAB = 'chat'
const STRATEGIES_TAB = 'strategies'

function toWizardValue(product: {
  name: string
  kind: string
  icp_form: Record<string, unknown>
}) {
  const { form_version: _formVersion, ...formBody } = product.icp_form
  return {
    identity: {
      name: product.name,
      kind: product.kind,
      thumbnail_url: (product as any).thumbnail_url,
    },
    ...productTemplate,
    ...formBody,
  }
}

function parseTab(value: string | null) {
  if (value === DETAILS_TAB) return DETAILS_TAB
  if (value === CHAT_TAB) return CHAT_TAB
  return STRATEGIES_TAB
}

export function ProductDetailPage() {
  const { orgId = '', productId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const { error, load, loading, product, reset, save, saved, submitting } = useProductDetailStore()
  const tab = parseTab(searchParams.get('tab'))
  const [editModalOpen, setEditModalOpen] = useState(false)
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

  // Clear URL edit mode just in case there's an old link
  useEffect(() => {
    if (searchParams.get('mode') === 'edit') {
      const next = new URLSearchParams(searchParams)
      next.delete('mode')
      setSearchParams(next, { replace: true })
      setEditModalOpen(true)
    }
  }, [searchParams, setSearchParams])

  useEffect(() => {
    if (saved) {
      setEditModalOpen(false)
    }
  }, [saved])

  const setTab = (nextTab: string) => {
    const next = new URLSearchParams(searchParams)
    if (nextTab === STRATEGIES_TAB) {
      next.delete('tab')
    } else if (nextTab === CHAT_TAB) {
      next.set('tab', CHAT_TAB)
    } else {
      next.set('tab', DETAILS_TAB)
      
      if (useProductChatStore.getState().profileDirtyFromChat) {
        useProductChatStore.getState().clearDirtyFlag()
        void load(productId)
      }
    }
    setSearchParams(next, { replace: true })
  }

  const handleSave = async (value: Record<string, unknown>) => {
    await save(productId, value)
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
            ) : tab === DETAILS_TAB ? (
              <Button type="button" variant="ghost" onClick={() => setEditModalOpen(true)}>
                Edit
              </Button>
            ) : null}
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
                value: CHAT_TAB,
                label: 'Chat',
                content: <ProductChatTab />,
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
                  />
                ),
              },
            ]}
          />

          <EntityEditModal
            open={editModalOpen}
            onOpenChange={setEditModalOpen}
            title="product or service"
            sections={productFormSections}
            themes={productFormThemes}
            initialValue={toWizardValue(product)}
            submitting={submitting}
            serverError={error}
            onSubmit={handleSave}
          />
        </>
      )}
    </>
  )
}
