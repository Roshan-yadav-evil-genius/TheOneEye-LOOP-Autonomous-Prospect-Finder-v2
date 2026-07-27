import { useEffect, useState, useCallback } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { SplitFormChatLayout } from '../../../shared/components/split-form-chat-layout'
import { FormLiveEditor } from '../../forms/components/form-live-editor'
import { UploadContext } from '../../forms/contexts/upload-context'
import { strategyTemplate } from '../../forms/form-definitions'
import { strategyFormSections } from '../../forms/form-field-schema'
import { strategyFormThemes } from '../../forms/form-themes'
import { organizationsApi } from '../../organizations/api/organizations-api'
import { productsApi } from '../../products/api/products-api'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'
import { salesStrategyApi, type SalesStrategy } from '../api/sales-strategy-api'
import { useStrategyChatStore } from '../stores/strategy-chat-store'

function toFormValue(strategy: SalesStrategy) {
  const form = (strategy.sales_strategy_form ?? {}) as Record<string, unknown>
  const overview =
    form.overview && typeof form.overview === 'object'
      ? (form.overview as Record<string, unknown>)
      : {}
  const runTargets =
    form.run_targets && typeof form.run_targets === 'object'
      ? (form.run_targets as Record<string, unknown>)
      : {}

  return {
    ...strategyTemplate,
    ...form,
    overview: {
      ...overview,
      name: typeof overview.name === 'string' && overview.name ? overview.name : strategy.name,
      thumbnail_url: (strategy as any).thumbnail_url ?? overview.thumbnail_url ?? '',
    },
    run_targets: {
      ...runTargets,
      target_companies: strategy.target_companies,
      contacts_per_company_default: strategy.contacts_per_company_default,
    },
  }
}

export function StrategyEditPage() {
  const { orgId = '', productId = '', strategyId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const sectionParam = searchParams.get('section') ?? searchParams.get('step') ?? undefined
  const themeParam = searchParams.get('theme') ?? undefined
  const [strategy, setStrategy] = useState<SalesStrategy | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [saved, setSaved] = useState(false)
  const chatStore = useStrategyChatStore()
  const [parentOrg, setParentOrg] = useState<any>(null)
  const [parentProduct, setParentProduct] = useState<any>(null)

  useEffect(() => {
    let cancelled = false
    if (orgId) {
      void organizationsApi
        .getOrganization(orgId)
        .then((org) => {
          if (!cancelled) setParentOrg(org)
        })
        .catch(() => {})
    }
    if (productId) {
      void productsApi
        .getProduct(productId)
        .then((prod) => {
          if (!cancelled) setParentProduct(prod)
        })
        .catch(() => {})
    }
    return () => {
      cancelled = true
    }
  }, [orgId, productId])

  const loadStrategy = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await salesStrategyApi.getStrategy(id)
      setStrategy(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load strategy.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadStrategy(strategyId)
    void chatStore.loadHistory(strategyId)
  }, [strategyId, loadStrategy])

  // Live synchronization: When AI Agent executes set_sales_strategy, reload form
  useEffect(() => {
    if (chatStore.profileDirtyFromChat) {
      chatStore.clearDirtyFlag()
      void loadStrategy(strategyId)
    }
  }, [chatStore.profileDirtyFromChat, chatStore, loadStrategy, strategyId])

  const handleSave = async (value: Record<string, unknown>) => {
    setSubmitting(true)
    setError(null)
    setSaved(false)
    try {
      const overview = (value.overview as Record<string, unknown>) ?? {}
      const updated = await salesStrategyApi.updateStrategyProfile(strategyId, {
        form: value,
        name: typeof overview.name === 'string' && overview.name ? overview.name : null,
      })
      setStrategy(updated)
      setSaved(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save strategy.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && !strategy) {
    return <p className="muted">Loading sales strategy profile…</p>
  }

  if (error && !strategy) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return (
    <SplitFormChatLayout
      title={`Edit Strategy: ${strategy?.name ?? ''}`}
      subtitle="Interactive split-panel mode. Manually edit strategy fields or work with the AI assistant."
      breadcrumbs={[
        { label: 'Organizations', to: '/orgs' },
        { 
          label: parentOrg?.name ?? 'Organization', 
          to: `/orgs/${orgId}`,
          thumbnailUrl: parentOrg?.thumbnail_url,
          fallbackThumbnailUrl: '/static/org_placeholder.png'
        },
        { 
          label: parentProduct?.name ?? 'Product', 
          to: `/orgs/${orgId}/products/${productId}`,
          thumbnailUrl: parentProduct?.thumbnail_url,
          fallbackThumbnailUrl: '/static/product_service_placeholder.png'
        },
        { 
          label: strategy?.name ?? 'Strategy', 
          to: `/orgs/${orgId}/products/${productId}/sales-strategies/${strategyId}`,
          thumbnailUrl: strategy ? (strategy as any).thumbnail_url : null,
          fallbackThumbnailUrl: '/static/strategy_placeholder.png'
        },
        { label: 'Edit' },
      ]}
      leftPanel={
        strategy ? (
          <UploadContext.Provider value={`/api/v1/orgs/${orgId}/products/${productId}/sales-strategies/${strategyId}/thumbnail`}>
            <FormLiveEditor
              formKey="sales-strategy"
              title="Sales Strategy Form"
              sections={strategyFormSections}
              themes={strategyFormThemes}
              initialValue={toFormValue(strategy)}
              initialSectionKey={sectionParam}
              initialThemeKey={themeParam}
              submitting={submitting}
              serverError={error}
              saved={saved}
              onSubmit={handleSave}
            />
          </UploadContext.Provider>
        ) : null
      }
      rightPanel={
        <SetupChatPanel
          title="Sales Strategy Assistant"
          threadId={`strat-${strategyId}`}
          entityId={strategyId}
          agentDescription="Guides you in targeting, signals, and outreach strategy definition."
          store={chatStore}
        />
      }
    />
  )
}
