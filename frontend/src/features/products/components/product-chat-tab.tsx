import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useProductChatStore } from '../stores/product-chat-store'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'

export function ProductChatTab() {
  const { productId = '' } = useParams()
  const store = useProductChatStore()

  const { loadHistory, reset } = store

  useEffect(() => {
    void loadHistory(productId)
    return () => reset()
  }, [productId, loadHistory, reset])

  return (
    <SetupChatPanel 
      title="Product Setup Assistant"
      threadId={`product_${productId}_setup_chat`}
      entityId={productId}
      agentDescription="can update product profile; switch to Details tab to see saved fields"
      store={store}
    />
  )
}
