import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { FormProfileViewer } from '../../forms/components/form-profile-viewer'
import { strategyTemplate } from '../../forms/form-definitions'
import { strategyFormSections } from '../../forms/form-field-schema'
import { strategyFormThemes } from '../../forms/form-themes'
import {
  type SalesStrategy,
  salesStrategyApi,
} from '../api/sales-strategy-api'
import { WorkspaceShell } from '../components/workspace-shell'
import { useStrategyChatStore } from '../stores/strategy-chat-store'

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

  return (
    <WorkspaceShell pageSubtitle="Full strategy profile for this run (immutable).">
      {error ? <p role="alert" className="error-banner">{error}</p> : null}
      {!strategy && !error ? <p className="muted">Loading strategy…</p> : null}
      {strategy ? (
        <FormProfileViewer
          title="Strategy profile"
          validated
          sections={strategyFormSections}
          themes={strategyFormThemes}
          value={toViewerValue(strategy)}
          hint="Immutable after creation — operators cannot edit strategy fields here. Use the Agent Chat to update the strategy."
          actions={
            <span className="muted">
              Company finder attempt {strategy.company_finder_attempt}/
              {strategy.target_companies}
            </span>
          }
        />
      ) : null}
    </WorkspaceShell>
  )
}
