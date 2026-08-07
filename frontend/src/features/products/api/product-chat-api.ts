import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  type StateSnapshotRead,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const productChatApi = {
  getHistory: async (productId: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (await apiClient.get<ChatHistoryRead>(`/api/v1/products/${productId}/chat/history${queryString}`)).data
  },

  getStateHistory: async (productId: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (await apiClient.get<StateSnapshotRead[]>(`/api/v1/products/${productId}/chat/state-history${queryString}`)).data
  },

  clearChat: async (productId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/products/${productId}/chat${params}`)
  },

  deleteMessage: async (productId: string, messageId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/products/${productId}/chat/messages/${encodeURIComponent(messageId)}${params}`)
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
