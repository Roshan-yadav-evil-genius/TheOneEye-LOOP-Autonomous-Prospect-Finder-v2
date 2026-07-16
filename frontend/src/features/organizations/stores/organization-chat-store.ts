import { createSetupChatStore } from '../../setup-chat/stores/store-factory'
import { organizationsChatApi } from '../api/organizations-chat-api'

export const useOrganizationChatStore = createSetupChatStore(organizationsChatApi)
