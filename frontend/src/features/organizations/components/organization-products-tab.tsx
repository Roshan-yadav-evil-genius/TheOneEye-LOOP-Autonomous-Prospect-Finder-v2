import { Link, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useProductsStore } from '../../products/stores/products-store'
import { Button } from '../../../shared/components/button'
import { EmptyState } from '../../../shared/components/design-system'
import { EntityList, EntityListItem } from '../../../shared/components/entity-list'
import { EntityEditModal } from '../../forms/components/entity-edit-modal'
import { productTemplate } from '../../forms/form-definitions'
import { productFormSections } from '../../forms/form-field-schema'
import { productFormThemes } from '../../forms/form-themes'
import { productsApi } from '../../products/api/products-api'

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

export function OrganizationProductsTab() {
  const { orgId = '' } = useParams()
  const { error, load, loading, products } = useProductsStore()
  const [editingProductId, setEditingProductId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    void load(orgId)
  }, [load, orgId])

  const editingProduct = products.find((p) => p.id === editingProductId)

  const handleSave = async (value: Record<string, unknown>) => {
    if (!editingProductId) return
    setSubmitting(true)
    setSaveError(null)
    try {
      await productsApi.updateProductProfile(editingProductId, {
        form: value,
      })
      setEditingProductId(null)
      void load(orgId)
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save product.')
    } finally {
      setSubmitting(false)
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
      <EntityList>
        {products.map((product) => (
          <EntityListItem
            key={product.id}
            title={product.name}
            to={`/orgs/${orgId}/products/${product.id}`}
            onEdit={() => setEditingProductId(product.id)}
            editLabel={`Edit ${product.name}`}
            badge={product.profile_validated ? 'validated' : 'incomplete'}
            badgeTone={product.profile_validated ? 'success' : 'warning'}
            meta={`${product.kind} · open details or strategies`}
            thumbnailUrl={product.thumbnail_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'}${product.thumbnail_url}` : '/static/product_service_placeholder.png'}
          />
        ))}
      </EntityList>

      {editingProduct ? (
        <EntityEditModal
          open={!!editingProductId}
          onOpenChange={(open) => !open && setEditingProductId(null)}
          title="product or service"
          sections={productFormSections}
          themes={productFormThemes}
          initialValue={toWizardValue(editingProduct as any)}
          submitting={submitting}
          serverError={saveError}
          onSubmit={handleSave}
        />
      ) : null}
    </>
  )
}
