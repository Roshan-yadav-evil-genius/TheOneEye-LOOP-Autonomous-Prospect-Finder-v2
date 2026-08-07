import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  type StateSnapshotRead,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const strategyChatApi = {
  getHistory: async (strategyId: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (await apiClient.get<ChatHistoryRead>(`/api/v1/sales-strategies/${strategyId}/chat/history${queryString}`)).data
  },

  getStateHistory: async (strategyId: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (await apiClient.get<StateSnapshotRead[]>(`/api/v1/sales-strategies/${strategyId}/chat/state-history${queryString}`)).data
  },

  clearChat: async (strategyId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/sales-strategies/${strategyId}/chat${params}`)
  },

  deleteMessage: async (strategyId: string, messageId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(`/api/v1/sales-strategies/${strategyId}/chat/messages/${encodeURIComponent(messageId)}${params}`)
  },

  streamChat: async (
    strategyId: string,
    data: ChatStreamRequest,
    onEvent: (event: ChatStreamEvent) => void
  ) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'
    const url = `${baseUrl.replace(/\/$/, '')}/api/v1/sales-strategies/${strategyId}/chat/stream`
    return streamChatGeneric(url, data, onEvent)
  },

  getThreads: async (strategyId: string): Promise<string[]> =>
    (await apiClient.get<string[]>(`/api/v1/sales-strategies/${strategyId}/chat/threads`)).data,

  newThread: async (strategyId: string): Promise<{ thread_id: string }> =>
    (await apiClient.post<{ thread_id: string }>(`/api/v1/sales-strategies/${strategyId}/chat/new-thread`)).data,
}
