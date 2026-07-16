import { createSetupChatStore } from '../../setup-chat/stores/store-factory'
import { strategyChatApi } from '../api/strategy-chat-api'

export const useStrategyChatStore = createSetupChatStore(strategyChatApi)
