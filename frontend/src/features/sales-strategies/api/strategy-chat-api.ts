import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const strategyChatApi = {
  getHistory: async (strategyId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return (await apiClient.get<ChatHistoryRead>(`/api/v1/sales-strategies/${strategyId}/chat/history${params}`)).data
  },

  clearChat: async (strategyId: string) =>
    await apiClient.delete(`/api/v1/sales-strategies/${strategyId}/chat`),

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
