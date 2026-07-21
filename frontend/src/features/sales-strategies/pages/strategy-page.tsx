import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { EntityEditModal } from '../../forms/components/entity-edit-modal'
import { strategyTemplate } from '../../forms/form-definitions'
import { strategyFormSections } from '../../forms/form-field-schema'
import { strategyFormThemes } from '../../forms/form-themes'
import {
  type SalesStrategy,
  salesStrategyApi,
} from '../api/sales-strategy-api'
import { WorkspaceShell } from '../components/workspace-shell'
import { useStrategyChatStore } from '../stores/strategy-chat-store'
import { UploadContext } from '../../forms/contexts/upload-context'
import { Button } from '../../../shared/components/button'

function toViewerValue(strategy: SalesStrategy) {
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

export function StrategyPage() {
  const { strategyId = '' } = useParams()
  const [strategy, setStrategy] = useState<SalesStrategy | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const loadStrategy = (id: string) => {
    let cancelled = false
    setError(null)
    void salesStrategyApi
      .getStrategy(id)
      .then((next) => {
        if (!cancelled) setStrategy(next)
      })
      .catch(() => {
        if (!cancelled) setError('Unable to load this sales strategy.')
      })
    return () => {
      cancelled = true
    }
  }

  useEffect(() => {
    const cleanup = loadStrategy(strategyId)
    // Clear the dirty flag when we render Details since we just loaded fresh data
    useStrategyChatStore.getState().clearDirtyFlag()
    return cleanup
  }, [strategyId])

  const handleSave = async (value: Record<string, unknown>) => {
    setSubmitting(true)
    setSaveError(null)
    try {
      const overview = (value.overview as Record<string, unknown>) ?? {}
      await salesStrategyApi.updateStrategyProfile(strategyId, {
        form: value,
        name: typeof overview.name === 'string' && overview.name ? overview.name : null,
      })
      setEditModalOpen(false)
      loadStrategy(strategyId)
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save strategy.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <WorkspaceShell 
      pageSubtitle="Full strategy profile for this run."
      actions={
        strategy ? (
          <Button type="button" variant="ghost" onClick={() => setEditModalOpen(true)}>
            Edit
          </Button>
        ) : null
      }
    >
      {error ? <p role="alert" className="error-banner">{error}</p> : null}
      {!strategy && !error ? <p className="muted">Loading strategy…</p> : null}
      {strategy ? (
        <>
          <FormProfileViewer
            title="Strategy profile"
            validated
            sections={strategyFormSections}
            themes={strategyFormThemes}
            value={toViewerValue(strategy)}
            actions={
              <div className="toolbar-row">
                Company finder attempt {strategy.company_finder_attempt}/
                {strategy.target_companies}
              </div>
            }
          />
          <UploadContext.Provider value={`/api/v1/orgs/${orgId}/products/${productId}/sales-strategies/${strategyId}/thumbnail`}>
            <EntityEditModal
              open={editModalOpen}
              onOpenChange={setEditModalOpen}
              title="sales strategy"
              sections={strategyFormSections}
              themes={strategyFormThemes}
              initialValue={toViewerValue(strategy)}
              submitting={submitting}
              serverError={saveError}
              onSubmit={handleSave}
            />
          </UploadContext.Provider>
        </>
      ) : null}
    </WorkspaceShell>
  )
}
