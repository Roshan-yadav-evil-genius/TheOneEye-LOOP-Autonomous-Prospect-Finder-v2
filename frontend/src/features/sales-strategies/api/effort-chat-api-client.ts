import { apiClient } from '../../../shared/api/client'
import {
  type ChatHistoryRead,
  type ChatStreamRequest,
  type ChatStreamEvent,
  type StateSnapshotRead,
  streamChatGeneric,
} from '../../setup-chat/api/setup-chat-api-client'
import type { SetupChatApi } from '../../setup-chat/stores/store-factory'

export const effortChatApi: SetupChatApi = {
  getHistory: async (effortPrefix: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (
      await apiClient.get<ChatHistoryRead>(
        `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat/history${queryString}`
      )
    ).data
  },

  getStateHistory: async (effortPrefix: string, threadId?: string | null, checkpoint_ns?: string | null) => {
    const searchParams = new URLSearchParams()
    if (threadId) searchParams.set('thread_id', threadId)
    if (checkpoint_ns) searchParams.set('checkpoint_ns', checkpoint_ns)
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : ''
    return (
      await apiClient.get<StateSnapshotRead[]>(
        `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat/state-history${queryString}`
      )
    ).data
  },

  clearChat: async (effortPrefix: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(
      `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat${params}`
    )
  },

  deleteMessage: async (effortPrefix: string, messageId: string, threadId?: string | null) => {
    const params = threadId ? `?thread_id=${encodeURIComponent(threadId)}` : ''
    return await apiClient.delete(
      `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat/messages/${encodeURIComponent(messageId)}${params}`
    )
  },

  streamChat: async (
    effortPrefix: string,
    data: ChatStreamRequest,
    onEvent: (event: ChatStreamEvent) => void
  ) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:7878'
    const url = `${baseUrl.replace(/\/$/, '')}/api/v1/efforts/${encodeURIComponent(
      effortPrefix
    )}/chat/stream`
    return streamChatGeneric(url, data, onEvent)
  },

  getThreads: async (effortPrefix: string): Promise<{ threads: string[]; namespaces?: Record<string, string[]> }> =>
    (
      await apiClient.get<{ threads: string[]; namespaces?: Record<string, string[]> }>(
        `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat/threads`
      )
    ).data,

  newThread: async (effortPrefix: string): Promise<{ thread_id: string }> =>
    (
      await apiClient.post<{ thread_id: string }>(
        `/api/v1/efforts/${encodeURIComponent(effortPrefix)}/chat/new-thread`
      )
    ).data,
}
