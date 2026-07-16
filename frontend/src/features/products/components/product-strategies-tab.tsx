import { Link, useParams } from 'react-router-dom'
import { useEffect } from 'react'

import { useStrategiesListStore } from '../../sales-strategies/stores/strategies-list-store'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'

export function ProductStrategiesTab() {
  const { orgId = '', productId = '' } = useParams()
  const { error, load, loading, strategies } = useStrategiesListStore()

  useEffect(() => {
    void load(productId)
  }, [load, productId])

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
    <EntityList>
      {strategies.map((strategy) => (
        <EntityListItem
          key={strategy.id}
          title={strategy.name}
          to={`/orgs/${orgId}/sales-strategies/${strategy.id}/companies`}
          badge={`${strategy.company_finder_attempt}/${strategy.target_companies}`}
          badgeTone="info"
          meta={`${strategy.contacts_per_company_default} contacts per company · strategy form is read-only after creation`}
        />
      ))}
    </EntityList>
  )
}
