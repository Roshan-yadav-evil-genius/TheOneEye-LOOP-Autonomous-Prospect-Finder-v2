import { create } from 'zustand'

import {
  organizationsChatApi,
  type ChatStreamEvent,
  type ChatStreamRequest
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
  
  incompleteTurn: boolean
  canResume: boolean
  lastUserMessage: string | null
  
  setMode: (mode: 'chat' | 'agent') => void
  loadHistory: (organizationId: string) => Promise<void>
  clearHistory: (organizationId: string) => Promise<void>
  send: (organizationId: string, message: string) => Promise<void>
  retry: (organizationId: string) => Promise<void>
  reset: () => void
  clearDirtyFlag: () => void
  
  _runStream: (organizationId: string, request: ChatStreamRequest) => Promise<void>
}

export const useOrganizationChatStore = create<ChatStoreState>((set, get) => ({
  mode: 'chat',
  messages: [],
  streaming: false,
  error: null,
  profileDirtyFromChat: false,
  incompleteTurn: false,
  canResume: false,
  lastUserMessage: null,

  setMode: (mode) => set({ mode }),

  reset: () => set({ 
    messages: [], 
    streaming: false, 
    error: null, 
    profileDirtyFromChat: false,
    incompleteTurn: false,
    canResume: false,
    lastUserMessage: null
  }),
  
  clearDirtyFlag: () => set({ profileDirtyFromChat: false }),

  loadHistory: async (organizationId) => {
    try {
      set({ error: null })
      const history = await organizationsChatApi.getHistory(organizationId)
      
      const messages: ChatUiMessage[] = []
      let lastUserMsg: string | null = null
      
      history.messages.forEach((m, i) => {
        if (m.role === 'tool_call') {
          messages.push({ id: `hist-${i}`, kind: 'tool_call', name: m.name || '', args: m.args || {} })
        } else if (m.role === 'tool_result') {
          messages.push({ id: `hist-${i}`, kind: 'tool_result', name: m.name || '', content: m.content })
        } else if (m.role === 'user') {
          lastUserMsg = m.content
          const lastMsg = messages[messages.length - 1]
          if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === m.content) {
            // Deduplicate consecutive identical user messages
            return
          }
          messages.push({ id: `hist-${i}`, kind: 'user', content: m.content })
        } else {
          messages.push({ id: `hist-${i}`, kind: 'assistant', content: m.content })
        }
      })
      
      set({ 
        messages, 
        lastUserMessage: lastUserMsg,
        incompleteTurn: history.can_resume,
        canResume: history.can_resume
      })
    } catch (e: any) {
      set({ error: e.message || 'Failed to load history' })
    }
  },

  clearHistory: async (organizationId) => {
    try {
      set({ error: null })
      await organizationsChatApi.clearChat(organizationId)
      set({ 
        messages: [],
        incompleteTurn: false,
        canResume: false,
        lastUserMessage: null
      })
    } catch (e: any) {
      set({ error: e.message || 'Failed to clear chat' })
    }
  },

  send: async (organizationId, message) => {
    const { mode, messages } = get()
    
    // add user message immediately
    const userMsg: ChatUiMessage = { id: `user-${Date.now()}`, kind: 'user', content: message }
    set({ messages: [...messages, userMsg], streaming: true, error: null, lastUserMessage: message })

    await get()._runStream(organizationId, { message, mode })
  },
  
  retry: async (organizationId: string) => {
    const { mode, canResume, lastUserMessage } = get()
    set({ streaming: true, error: null })
    
    const redo_last = !canResume
    const message = (redo_last && lastUserMessage) ? lastUserMessage : ''
    
    await get()._runStream(organizationId, { message, mode, retry: true, redo_last })
  },

  _runStream: async (organizationId: string, request: ChatStreamRequest) => {
    let currentMessages = get().messages
    let activeAssistantMsgId = `ast-${Date.now()}`
    let activeReasoningId = `rsn-${Date.now()}`
    
    if (request.retry) {
      if (request.redo_last) {
        // Redo: trim the incomplete assistant/reasoning messages entirely so they don't stay forever
        while (currentMessages.length > 0) {
          const last = currentMessages[currentMessages.length - 1]
          if (last.kind !== 'user' && last.kind !== 'tool_result' && last.kind !== 'tool_call') {
            currentMessages = currentMessages.slice(0, -1)
          } else {
            break
          }
        }
      } else {
        // Resume: reuse message IDs to prevent stacking partial and full answers
        // Also clear the partial text before restarting the stream!
        const reversed = [...currentMessages].reverse()
        const lastReasoning = reversed.find(m => m.kind === 'reasoning' || m.kind === 'user' || m.kind === 'tool_result')
        if (lastReasoning?.kind === 'reasoning') {
          activeReasoningId = lastReasoning.id
          currentMessages = currentMessages.map(m => m.id === activeReasoningId ? { ...m, text: '' } : m)
        }
        const lastAssistant = reversed.find(m => m.kind === 'assistant' || m.kind === 'user' || m.kind === 'tool_result')
        if (lastAssistant?.kind === 'assistant') {
          activeAssistantMsgId = lastAssistant.id
          currentMessages = currentMessages.map(m => m.id === activeAssistantMsgId ? { ...m, content: '' } : m)
        }
      }
    }
    
    const appendOrUpdate = (updater: (msgs: ChatUiMessage[]) => ChatUiMessage[]) => {
      currentMessages = updater(currentMessages)
      set({ messages: currentMessages })
    }

    try {
      await organizationsChatApi.streamChat(
        organizationId,
        request,
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
              set({ error: event.message, incompleteTurn: true, canResume: event.can_resume ?? false })
              break
            case 'incomplete':
              set({ incompleteTurn: true, canResume: event.can_resume })
              break
            case 'done':
              set({ incompleteTurn: false, canResume: false })
              break
          }
        }
      )
    } catch (e: any) {
      set({ error: e.message || 'Stream failed', incompleteTurn: true, canResume: get().canResume })
    } finally {
      set({ streaming: false })
    }
  }
}))
