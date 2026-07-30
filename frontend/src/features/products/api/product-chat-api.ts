import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const productChatApi = {
  getHistory: async (productId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return (await apiClient.get<ChatHistoryRead>(`/api/v1/products/${productId}/chat/history${params}`)).data
  },

  clearChat: async (productId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/products/${productId}/chat${params}`)
  },

  streamChat: async (
    productId: string,
    data: ChatStreamRequest,
    onEvent: (event: ChatStreamEvent) => void
  ) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'
    const url = `${baseUrl.replace(/\/$/, '')}/api/v1/products/${productId}/chat/stream`
    return streamChatGeneric(url, data, onEvent)
  },

  getThreads: async (productId: string): Promise<string[]> =>
    (await apiClient.get<string[]>(`/api/v1/products/${productId}/chat/threads`)).data,

  newThread: async (productId: string): Promise<{ thread_id: string }> =>
    (await apiClient.post<{ thread_id: string }>(`/api/v1/products/${productId}/chat/new-thread`)).data,
}
