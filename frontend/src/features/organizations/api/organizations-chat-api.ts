import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const organizationsChatApi = {
  getHistory: async (organizationId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return (await apiClient.get<ChatHistoryRead>(`/api/v1/organizations/${organizationId}/chat/history${params}`)).data
  },

  clearChat: async (organizationId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/organizations/${organizationId}/chat${params}`)
  },

  streamChat: async (
    organizationId: string,
    data: ChatStreamRequest,
    onEvent: (event: ChatStreamEvent) => void
  ) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'
    const url = `${baseUrl.replace(/\/$/, '')}/api/v1/organizations/${organizationId}/chat/stream`
    return streamChatGeneric(url, data, onEvent)
  },

  getThreads: async (organizationId: string): Promise<string[]> =>
    (await apiClient.get<string[]>(`/api/v1/organizations/${organizationId}/chat/threads`)).data,

  newThread: async (organizationId: string): Promise<{ thread_id: string }> =>
    (await apiClient.post<{ thread_id: string }>(`/api/v1/organizations/${organizationId}/chat/new-thread`)).data,
}
