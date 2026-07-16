import { create } from 'zustand'

import {
  organizationsChatApi,
  type ChatStreamEvent
} from '../api/organizations-chat-api'

export type ChatUiMessage =
  | { id: string; kind: 'user'; content: string }
  | { id: string; kind: 'assistant'; content: string }
  | { id: string; kind: 'reasoning'; text: string }
  | { id: string; kind: 'tool_call'; name: string; args: unknown }
  | { id: string; kind: 'tool_result'; name: string; content: string }

interface ChatStoreState {
  mode: 'chat' | 'agent'
  messages: ChatUiMessage[]
  streaming: boolean
  error: string | null
  profileDirtyFromChat: boolean
  
  setMode: (mode: 'chat' | 'agent') => void
  loadHistory: (organizationId: string) => Promise<void>
  clearHistory: (organizationId: string) => Promise<void>
  send: (organizationId: string, message: string) => Promise<void>
  reset: () => void
  clearDirtyFlag: () => void
}

export const useOrganizationChatStore = create<ChatStoreState>((set, get) => ({
  mode: 'chat',
  messages: [],
  streaming: false,
  error: null,
  profileDirtyFromChat: false,

  setMode: (mode) => set({ mode }),

  reset: () => set({ messages: [], streaming: false, error: null, profileDirtyFromChat: false }),
  
  clearDirtyFlag: () => set({ profileDirtyFromChat: false }),

  loadHistory: async (organizationId) => {
    try {
      set({ error: null })
      const history = await organizationsChatApi.getHistory(organizationId)
      const messages: ChatUiMessage[] = history.messages.map((m, i) => ({
        id: `hist-${i}`,
        kind: m.role === 'user' ? 'user' : 'assistant',
        content: m.content
      }))
      set({ messages })
    } catch (e: any) {
      set({ error: e.message || 'Failed to load history' })
    }
  },

  clearHistory: async (organizationId) => {
    try {
      set({ error: null })
      await organizationsChatApi.clearChat(organizationId)
      set({ messages: [] })
    } catch (e: any) {
      set({ error: e.message || 'Failed to clear chat' })
    }
  },

  send: async (organizationId, message) => {
    const { mode, messages } = get()
    
    // add user message immediately
    const userMsg: ChatUiMessage = { id: `user-${Date.now()}`, kind: 'user', content: message }
    set({ messages: [...messages, userMsg], streaming: true, error: null })

    let currentMessages = get().messages
    let activeAssistantMsgId = `ast-${Date.now()}`
    let activeReasoningId = `rsn-${Date.now()}`
    
    // helper to update messages in place
    const appendOrUpdate = (updater: (msgs: ChatUiMessage[]) => ChatUiMessage[]) => {
      currentMessages = updater(currentMessages)
      set({ messages: currentMessages })
    }

    try {
      await organizationsChatApi.streamChat(
        organizationId,
        { message, mode },
        (event: ChatStreamEvent) => {
          switch (event.kind) {
            case 'reasoning':
              appendOrUpdate((msgs) => {
                const existing = msgs.find(m => m.id === activeReasoningId)
                if (existing && existing.kind === 'reasoning') {
                  return msgs.map(m => m.id === activeReasoningId && m.kind === 'reasoning' ? { ...m, text: m.text + event.text } : m)
                }
                return [...msgs, { id: activeReasoningId, kind: 'reasoning', text: event.text }]
              })
              break

            case 'content':
              appendOrUpdate((msgs) => {
                const existing = msgs.find(m => m.id === activeAssistantMsgId)
                if (existing && existing.kind === 'assistant') {
                  return msgs.map(m => m.id === activeAssistantMsgId && m.kind === 'assistant' ? { ...m, content: m.content + event.text } : m)
                }
                return [...msgs, { id: activeAssistantMsgId, kind: 'assistant', content: event.text }]
              })
              break

            case 'tool_call':
              appendOrUpdate((msgs) => [
                ...msgs,
                { id: `tc-${event.id}`, kind: 'tool_call', name: event.name, args: event.args }
              ])
              // prepare a new reasoning/assistant id for anything that follows
              activeReasoningId = `rsn-${Date.now()}`
              activeAssistantMsgId = `ast-${Date.now()}`
              break

            case 'tool_result':
              appendOrUpdate((msgs) => [
                ...msgs,
                { id: `tr-${event.id}`, kind: 'tool_result', name: event.name, content: event.content }
              ])
              
              if (event.name.startsWith('set_')) {
                set({ profileDirtyFromChat: true })
              }
              break

            case 'error':
              set({ error: event.message })
              break

            case 'done':
              // stream finished
              break
          }
        }
      )
    } catch (e: any) {
      set({ error: e.message || 'Stream failed' })
    } finally {
      set({ streaming: false })
    }
  }
}))
