import { createSetupChatStore } from '../../setup-chat/stores/store-factory'
import { effortChatApi } from '../api/effort-chat-api-client'

export const useEffortChatStore = createSetupChatStore(effortChatApi, 'effort_chat_mode')
