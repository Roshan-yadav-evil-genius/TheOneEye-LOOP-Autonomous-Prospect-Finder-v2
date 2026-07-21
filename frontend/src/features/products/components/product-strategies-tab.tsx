import { Link, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useStrategiesListStore } from '../../sales-strategies/stores/strategies-list-store'
import { UploadContext } from '../../forms/contexts/upload-context'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'
import { EntityEditModal } from '../../forms/components/entity-edit-modal'
import { strategyTemplate } from '../../forms/form-definitions'
import { strategyFormSections } from '../../forms/form-field-schema'
import { strategyFormThemes } from '../../forms/form-themes'
import { type SalesStrategy, salesStrategyApi } from '../../sales-strategies/api/sales-strategy-api'

function toWizardValue(strategy: SalesStrategy) {
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
      thumbnail_url: (strategy as any).thumbnail_url,
    },
    run_targets: {
      ...runTargets,
      target_companies: strategy.target_companies,
      contacts_per_company_default: strategy.contacts_per_company_default,
    },
  }
}

export function ProductStrategiesTab() {
  const { orgId = '', productId = '' } = useParams()
  const { error, load, loading, strategies } = useStrategiesListStore()
  const [editingStrategyId, setEditingStrategyId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    void load(productId)
  }, [load, productId])

  const editingStrategy = strategies.find((s) => s.id === editingStrategyId)

  const handleSave = async (value: Record<string, unknown>) => {
    if (!editingStrategyId) return
    setSubmitting(true)
    setSaveError(null)
    try {
      const overview = (value.overview as Record<string, unknown>) ?? {}
      await salesStrategyApi.updateStrategyProfile(editingStrategyId, {
        form: value,
        name: typeof overview.name === 'string' && overview.name ? overview.name : null,
      })
      setEditingStrategyId(null)
      void load(productId)
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save strategy.')
    } finally {
      setSubmitting(false)
    }
  }

  if (error) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  if (loading && strategies.length === 0) {
    return <p className="muted">Loading sales strategies…</p>
  }

  if (!loading && strategies.length === 0) {
    return (
      <EmptyState
        title="No sales strategies yet"
        body="Create a sales strategy for this product to open the workspace."
        action={
          <Button asChild>
            <Link to={`/orgs/${orgId}/products/${productId}/sales-strategies/new`}>
              New sales strategy
            </Link>
          </Button>
        }
      />
    )
  }

  return (
    <>
      <EntityList>
        {strategies.map((strategy) => (
          <EntityListItem
            key={strategy.id}
            title={strategy.name}
            to={`/orgs/${orgId}/sales-strategies/${strategy.id}/companies`}
            onEdit={() => setEditingStrategyId(strategy.id)}
            editLabel={`Edit ${strategy.name}`}
            badge={`${strategy.company_finder_attempt}/${strategy.target_companies}`}
            badgeTone="info"
            meta={`${strategy.contacts_per_company_default} contacts per company`}
            thumbnailUrl={strategy.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${strategy.thumbnail_url}` : '/static/strategy_placeholder.png'}
          />
        ))}
      </EntityList>

      {editingStrategy ? (
        <UploadContext.Provider value={`/api/v1/orgs/${orgId}/products/${productId}/sales-strategies/${editingStrategyId}/thumbnail`}>
          <EntityEditModal
            open={!!editingStrategyId}
            onOpenChange={(open) => !open && setEditingStrategyId(null)}
            title="sales strategy"
            sections={strategyFormSections}
            themes={strategyFormThemes}
            initialValue={toWizardValue(editingStrategy)}
            submitting={submitting}
            serverError={saveError}
            onSubmit={handleSave}
          />
        </UploadContext.Provider>
      ) : null}
    </>
  )
}
