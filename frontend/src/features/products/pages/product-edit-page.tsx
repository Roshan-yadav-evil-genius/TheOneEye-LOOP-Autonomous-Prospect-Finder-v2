import { useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { SplitFormChatLayout } from '../../../shared/components/split-form-chat-layout'
import { FormLiveEditor } from '../../forms/components/form-live-editor'
import { UploadContext } from '../../forms/contexts/upload-context'
import { productTemplate } from '../../forms/form-definitions'
import { productFormSections } from '../../forms/form-field-schema'
import { productFormThemes } from '../../forms/form-themes'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'
import { useProductChatStore } from '../stores/product-chat-store'
import { useProductDetailStore } from '../stores/product-detail-store'

function toFormValue(product: {
  name: string
  kind: string
  icp_form: Record<string, unknown>
}) {
  return {
    identity: {
      name: product.name,
      kind: product.kind,
      thumbnail_url: (product as any).thumbnail_url,
    },
    ...productTemplate,
    ...product.icp_form,
  }
}

export function ProductEditPage() {
  const { orgId = '', productId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const sectionParam = searchParams.get('section') ?? searchParams.get('step') ?? undefined
  const themeParam = searchParams.get('theme') ?? undefined
  const { product, loading, error, submitting, saved, load, save, reset } = useProductDetailStore()
  const chatStore = useProductChatStore()

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
        { label: 'Organization', to: `/orgs/${orgId}` },
        { label: product?.name ?? 'Product', to: `/orgs/${orgId}/products/${productId}` },
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
              initialValue={toFormValue(product)}
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
