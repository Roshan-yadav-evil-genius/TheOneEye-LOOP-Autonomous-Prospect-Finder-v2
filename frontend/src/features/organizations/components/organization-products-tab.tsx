import { Link, useParams } from 'react-router-dom'
import { useEffect } from 'react'

import { useProductsStore } from '../../products/stores/products-store'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'

export function OrganizationProductsTab() {
  const { orgId = '' } = useParams()
  const { error, load, loading, products } = useProductsStore()

  useEffect(() => {
    void load(orgId)
  }, [load, orgId])

  if (error) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  if (loading && products.length === 0) {
    return <p className="muted">Loading products…</p>
  }

  if (!loading && products.length === 0) {
    return (
      <EmptyState
        title="No products yet"
        body="Validate the organization profile, then create a product or service before any sales strategy."
        action={
          <Button asChild>
            <Link to={`/orgs/${orgId}/products/new`}>New product</Link>
          </Button>
        }
      />
    )
  }

  return (
    <EntityList>
      {products.map((product) => (
        <EntityListItem
          key={product.id}
          title={product.name}
          to={`/orgs/${orgId}/products/${product.id}`}
          editTo={`/orgs/${orgId}/products/${product.id}?tab=details&mode=edit`}
          editLabel={`Edit ${product.name}`}
          badge={product.profile_validated ? 'validated' : 'incomplete'}
          badgeTone={product.profile_validated ? 'success' : 'warning'}
          meta={`${product.kind} · open details or strategies`}
          thumbnailUrl={product.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${product.thumbnail_url}` : '/static/product_service_placeholder.png'}
        />
      ))}
    </EntityList>
  )
}
