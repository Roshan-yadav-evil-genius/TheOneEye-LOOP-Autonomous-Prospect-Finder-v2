import { Link, useNavigate, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useStrategiesListStore } from '../../sales-strategies/stores/strategies-list-store'
import { salesStrategyApi } from '../../sales-strategies/api/sales-strategy-api'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'

export function ProductStrategiesTab() {
  const { orgId = '', productId = '' } = useParams()
  const navigate = useNavigate()
  const { error, load, loading, strategies } = useStrategiesListStore()
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    void load(productId)
  }, [load, productId])

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return
    setDeleteError(null)
    try {
      await salesStrategyApi.deleteStrategy(id)
      void load(productId)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete strategy.')
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
      {deleteError ? <p role="alert" className="error-banner">{deleteError}</p> : null}
      <EntityList>
        {strategies.map((strategy) => {
          const hasNoChildren = ((strategy as any).companies_count ?? 0) === 0
          return (
            <EntityListItem
              key={strategy.id}
              title={strategy.name}
              to={`/orgs/${orgId}/sales-strategies/${strategy.id}/companies`}
              onEdit={() =>
                navigate(
                  `/orgs/${orgId}/products/${productId}/sales-strategies/${strategy.id}/edit`,
                )
              }
              editLabel={`Edit ${strategy.name}`}
              onDelete={hasNoChildren ? () => handleDelete(strategy.id, strategy.name) : undefined}
              deleteLabel={`Delete ${strategy.name}`}
              badge={`${strategy.company_finder_attempt}/${strategy.target_companies}`}
              badgeTone="info"
              meta={`${strategy.contacts_per_company_default} contacts per company`}
              thumbnailUrl={strategy.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${strategy.thumbnail_url}` : '/static/strategy_placeholder.png'}
            />
          )
        })}
      </EntityList>
    </>
  )
}
