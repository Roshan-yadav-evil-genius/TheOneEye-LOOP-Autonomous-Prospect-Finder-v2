import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { SectionWizard } from '../../forms/components/section-wizard'
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

/** Edit is opened from the products list edit icon via `?mode=edit`. */

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

function parseTab(value: string | null, mode: string | null) {
  if (value === DETAILS_TAB || mode === 'edit') return DETAILS_TAB
  if (value === CHAT_TAB) return CHAT_TAB
  return STRATEGIES_TAB
}

export function ProductDetailPage() {
  const { orgId = '', productId = '' } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const { error, load, loading, product, reset, save, incrementalSave, saved, submitting } = useProductDetailStore()
  const tab = parseTab(searchParams.get('tab'), searchParams.get('mode'))
  const [mode, setMode] = useState<'view' | 'edit'>(
    searchParams.get('mode') === 'edit' ? 'edit' : 'view',
  )
  const [orgName, setOrgName] = useState<string | null>(null)

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
        if (!cancelled) setOrgName(organization.name)
      })
      .catch(() => {
        if (!cancelled) setOrgName(null)
      })
    return () => {
      cancelled = true
    }
  }, [orgId])

  useEffect(() => {
    setMode(searchParams.get('mode') === 'edit' ? 'edit' : 'view')
  }, [productId, searchParams])

  useEffect(() => {
    if (searchParams.get('mode') !== 'edit' || searchParams.get('tab') === DETAILS_TAB) return
    const next = new URLSearchParams(searchParams)
    next.set('tab', DETAILS_TAB)
    setSearchParams(next, { replace: true })
  }, [productId, searchParams, setSearchParams])

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
    if (nextTab === STRATEGIES_TAB) {
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
      
      if (useProductChatStore.getState().profileDirtyFromChat) {
        useProductChatStore.getState().clearDirtyFlag()
        void load(productId)
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
        title={product?.name ?? 'Product details'}
        subtitle="Full product profile and sales strategies for this offering."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { label: orgName ?? 'Organization', to: `/orgs/${orgId}` },
          { label: product?.name ?? 'Product' },
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
            ) : mode === 'edit' ? (
              <Button type="button" variant="ghost" onClick={cancelEdit}>
                Cancel edit
              </Button>
            ) : null}
          </>
        }
      />
      {error && tab === DETAILS_TAB && mode === 'edit' ? (
        <p role="alert" className="error-banner">
          {error}
        </p>
      ) : null}
      {loading || !product ? (
        <p className="muted">Loading product…</p>
      ) : (
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
              content:
                mode === 'view' ? (
                  <FormProfileViewer
                    title="Product profile"
                    validated={product.profile_validated}
                    sections={productFormSections}
                    themes={productFormThemes}
                    value={toWizardValue(product)}
                  />
                ) : (
                  <SectionWizard
                    key={`${product.id}-edit-${product.profile_validated}`}
                    title="product or service"
                    sections={productFormSections}
                    themes={productFormThemes}
                    initialValue={toWizardValue(product)}
                    submitLabel="Save product"
                    submitting={submitting}
                    serverError={error}
                    onSubmit={(value) => save(productId, value)}
                    onIncrementalSave={(value) => incrementalSave(productId, value)}
                  />
                ),
            },
          ]}
        />
      )}
    </>
  )
}
