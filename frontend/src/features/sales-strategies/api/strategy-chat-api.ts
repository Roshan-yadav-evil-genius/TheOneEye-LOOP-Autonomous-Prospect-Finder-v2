import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  streamChatGeneric
} from '../../setup-chat/api/setup-chat-api-client'

export const strategyChatApi = {
  getHistory: async (strategyId: string) =>
    (await apiClient.get<ChatHistoryRead>(`/api/v1/sales-strategies/${strategyId}/chat/history`)).data,

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
  }
}
