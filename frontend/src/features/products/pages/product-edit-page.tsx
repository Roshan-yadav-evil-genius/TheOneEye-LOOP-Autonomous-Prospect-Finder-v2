import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { SplitFormChatLayout } from '../../../shared/components/split-form-chat-layout'
import { FormLiveEditor } from '../../forms/components/form-live-editor'
import { UploadContext } from '../../forms/contexts/upload-context'
import { productFormSections } from '../../forms/form-field-schema'
import { productFormThemes } from '../../forms/form-themes'
import { organizationsApi } from '../../organizations/api/organizations-api'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'
import { useProductChatStore } from '../stores/product-chat-store'
import { useProductDetailStore } from '../stores/product-detail-store'
import { toProductFormValue } from '../utils/icp-utils'

export function ProductEditPage() {
  const { orgId = '', productId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const sectionParam = searchParams.get('section') ?? searchParams.get('step') ?? undefined
  const themeParam = searchParams.get('theme') ?? undefined
  const { product, loading, error, submitting, saved, load, save, reset } = useProductDetailStore()
  const chatStore = useProductChatStore()
  const [parentOrg, setParentOrg] = useState<any>(null)

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
    return () => {
      cancelled = true
    }
  }, [orgId])

  useEffect(() => {
    reset()
    void load(productId)
    void chatStore.loadHistory(productId)
    return () => reset()
  }, [productId, load, reset])

  // Live synchronization: When AI Agent executes set_product, reload form
  useEffect(() => {
    if (chatStore.profileDirtyFromChat) {
      chatStore.clearDirtyFlag()
      void load(productId)
    }
  }, [chatStore.profileDirtyFromChat, chatStore, load, productId])

  const handleSave = async (value: Record<string, unknown>) => {
    await save(productId, value)
  }

  if (loading && !product) {
    return <p className="muted">Loading product profile…</p>
  }

  if (error && !product) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return (
    <SplitFormChatLayout
      title={`Edit Product: ${product?.name ?? ''}`}
      subtitle="Interactive split-panel mode. Manually edit ICP fields or work with the AI assistant."
      breadcrumbs={[
        { label: 'Organizations', to: '/orgs' },
        { 
          label: parentOrg?.name ?? 'Organization', 
          to: `/orgs/${orgId}`,
          thumbnailUrl: parentOrg?.thumbnail_url,
          fallbackThumbnailUrl: '/static/org_placeholder.png'
        },
        { 
          label: product?.name ?? 'Product', 
          to: `/orgs/${orgId}/products/${productId}`,
          thumbnailUrl: product ? (product as any).thumbnail_url : null,
          fallbackThumbnailUrl: '/static/product_service_placeholder.png'
        },
        { label: 'Edit' },
      ]}
      leftPanel={
        product ? (
          <UploadContext.Provider value={`/api/v1/orgs/${orgId}/products/${productId}/thumbnail`}>
            <FormLiveEditor
              formKey="product"
              title="Product & ICP Form"
              sections={productFormSections}
              themes={productFormThemes}
              initialValue={toProductFormValue(product)}
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
          title="Product Assistant"
          threadId={`prod-${productId}`}
          entityId={productId}
          agentDescription="Guides you in defining ideal customer profiles and value propositions."
          store={chatStore}
        />
      }
    />
  )
}
