import { Link, useNavigate, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useProductsStore } from '../../products/stores/products-store'
import { productsApi } from '../../products/api/products-api'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'

export function OrganizationProductsTab() {
  const { orgId = '' } = useParams()
  const navigate = useNavigate()
  const { error, load, loading, products } = useProductsStore()
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    void load(orgId)
  }, [load, orgId])

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return
    setDeleteError(null)
    try {
      await productsApi.deleteProduct(id)
      void load(orgId)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete product.')
    }
  }

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
    <>
      {deleteError ? <p role="alert" className="error-banner">{deleteError}</p> : null}
      <EntityList>
        {products.map((product) => {
          const hasNoChildren = (product.strategies_count ?? 0) === 0
          return (
            <EntityListItem
              key={product.id}
              title={product.name}
              to={`/orgs/${orgId}/products/${product.id}`}
              onEdit={() => navigate(`/orgs/${orgId}/products/${product.id}/edit`)}
              editLabel={`Edit ${product.name}`}
              onDelete={hasNoChildren ? () => handleDelete(product.id, product.name) : undefined}
              deleteLabel={`Delete ${product.name}`}
              badge={product.profile_validated ? 'validated' : 'incomplete'}
              badgeTone={product.profile_validated ? 'success' : 'warning'}
              meta={`${product.kind} · open details or strategies`}
              thumbnailUrl={product.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${product.thumbnail_url}` : '/static/product_service_placeholder.png'}
            />
          )
        })}
      </EntityList>
    </>
  )
}
