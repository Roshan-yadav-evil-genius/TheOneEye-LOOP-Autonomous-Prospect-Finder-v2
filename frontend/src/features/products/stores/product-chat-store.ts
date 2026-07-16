import { createSetupChatStore } from '../../setup-chat/stores/store-factory'
import { productChatApi } from '../api/product-chat-api'

export const useProductChatStore = createSetupChatStore(productChatApi)
