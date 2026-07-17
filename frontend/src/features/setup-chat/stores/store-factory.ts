import { create, type StoreApi, type UseBoundStore } from 'zustand'

import {
  type ChatStreamEvent,
  type ChatStreamRequest,
  type ChatHistoryRead
} from '../api/setup-chat-api-client'

export type ChatUiMessage =
  | { id: string; kind: 'user'; content: string }
  | { id: string; aiMessageId?: string; kind: 'assistant'; content: string; metadata?: Record<string, any> }
  | { id: string; aiMessageId?: string; kind: 'reasoning'; text: string; metadata?: Record<string, any> }
  | { id: string; aiMessageId?: string; kind: 'tool_call'; name: string; args: unknown; metadata?: Record<string, any> }
  | { id: string; kind: 'tool_result'; name: string; content: string }

export interface SetupChatStoreState {
  mode: 'chat' | 'agent'
  messages: ChatUiMessage[]
  streaming: boolean
  error: string | null
  profileDirtyFromChat: boolean
  
  incompleteTurn: boolean
  canResume: boolean
  lastUserMessage: string | null
  
  setMode: (mode: 'chat' | 'agent') => void
  loadHistory: (entityId: string) => Promise<void>
  clearHistory: (entityId: string) => Promise<void>
  send: (entityId: string, message: string) => Promise<void>
  retry: (entityId: string) => Promise<void>
  reset: () => void
  clearDirtyFlag: () => void
  
  _runStream: (entityId: string, request: ChatStreamRequest) => Promise<void>
}

export interface SetupChatApi {
  getHistory: (entityId: string) => Promise<ChatHistoryRead>
  clearChat: (entityId: string) => Promise<any>
  streamChat: (entityId: string, request: ChatStreamRequest, onEvent: (event: ChatStreamEvent) => void) => Promise<void>
}

export function createSetupChatStore(api: SetupChatApi): UseBoundStore<StoreApi<SetupChatStoreState>> {
  return create<SetupChatStoreState>((set, get) => ({
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

    loadHistory: async (entityId) => {
      try {
        set({ error: null })
        const history = await api.getHistory(entityId)
        
        const messages: ChatUiMessage[] = []
        let lastUserMsg: string | null = null
        
        history.messages.forEach((msgDict: any, i: number) => {
          const type = msgDict.type
          const data = msgDict.data || {}
          
          if (type === 'human') {
            const content = typeof data.content === 'string' ? data.content : JSON.stringify(data.content)
            lastUserMsg = content
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === content) {
              return
            }
            messages.push({ id: `hist-${i}`, kind: 'user', content })
          } else if (type === 'ai') {
            const aiMessageId = msgDict.id || data.id || `hist-${i}`
            const meta: any = { raw: msgDict }
            if (data.usage_metadata) meta.usage_metadata = data.usage_metadata
            if (data.response_metadata) meta.response_metadata = data.response_metadata
            if (aiMessageId) meta.id = aiMessageId

            let reasoning = data.additional_kwargs?.reasoning_content || data.additional_kwargs?.reasoning
            if (!reasoning && Array.isArray(data.content)) {
                const rBlock = data.content.find((b: any) => b.type === 'reasoning')
                if (rBlock) reasoning = rBlock.text
            }
            
            const toolCalls = data.tool_calls || []
            const contentStr = typeof data.content === 'string' ? data.content : JSON.stringify(data.content)
            
            const metadataObj = Object.keys(meta).length > 0 ? meta : undefined
            
            if (reasoning) {
              messages.push({ id: `hist-${i}-rsn`, aiMessageId, kind: 'reasoning', text: reasoning, metadata: metadataObj })
            }
            
            if (contentStr && contentStr !== '""' && contentStr !== '[]' && contentStr !== '"[]"') {
              messages.push({ id: `hist-${i}-ast`, aiMessageId, kind: 'assistant', content: contentStr, metadata: metadataObj })
            }
            
            toolCalls.forEach((tc: any, tcIdx: number) => {
              messages.push({ id: `hist-${i}-tc-${tcIdx}`, aiMessageId, kind: 'tool_call', name: tc.name, args: tc.args, metadata: metadataObj })
            })
            
            if (!reasoning && (!contentStr || contentStr === '""' || contentStr === '[]' || contentStr === '"[]"') && toolCalls.length === 0) {
              messages.push({ id: `hist-${i}-ast`, aiMessageId, kind: 'assistant', content: '', metadata: metadataObj })
            }
          } else if (type === 'tool') {
            messages.push({ id: `hist-${i}-tr`, kind: 'tool_result', name: data.name, content: typeof data.content === 'string' ? data.content : JSON.stringify(data.content) })
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

    clearHistory: async (entityId) => {
      try {
        set({ error: null })
        await api.clearChat(entityId)
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

    send: async (entityId, message) => {
      const { mode, messages } = get()
      
      const userMsg: ChatUiMessage = { id: `user-${Date.now()}`, kind: 'user', content: message }
      set({ messages: [...messages, userMsg], streaming: true, error: null, lastUserMessage: message })

      await get()._runStream(entityId, { message, mode })
    },
    
    retry: async (entityId: string) => {
      const { mode, canResume, lastUserMessage } = get()
      set({ streaming: true, error: null })
      
      const redo_last = !canResume
      const message = (redo_last && lastUserMessage) ? lastUserMessage : ''
      
      await get()._runStream(entityId, { message, mode, retry: true, redo_last })
    },

    _runStream: async (entityId: string, request: ChatStreamRequest) => {
      let currentMessages = get().messages
      let activeAiTurnId = `turn-${Date.now()}`
      let activeAssistantMsgId = `ast-${Date.now()}`
      let activeReasoningId = `rsn-${Date.now()}`
      
      if (request.retry) {
        if (request.redo_last) {
          while (currentMessages.length > 0) {
            const last = currentMessages[currentMessages.length - 1]
            if (last.kind !== 'user' && last.kind !== 'tool_result' && last.kind !== 'tool_call') {
              currentMessages = currentMessages.slice(0, -1)
            } else {
              break
            }
          }
        } else {
          const reversed = [...currentMessages].reverse()
          const lastAiMsg = reversed.find(m => (m.kind === 'assistant' || m.kind === 'reasoning' || m.kind === 'tool_call') && m.aiMessageId)
          if (lastAiMsg && lastAiMsg.kind !== 'user' && lastAiMsg.kind !== 'tool_result' && 'aiMessageId' in lastAiMsg && lastAiMsg.aiMessageId) {
            activeAiTurnId = lastAiMsg.aiMessageId
          }
          
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
        await api.streamChat(
          entityId,
          request,
          (event: ChatStreamEvent) => {
            switch (event.kind) {
              case 'reasoning':
                appendOrUpdate((msgs) => {
                  const existing = msgs.find(m => m.id === activeReasoningId)
                  if (existing && existing.kind === 'reasoning') {
                    return msgs.map(m => m.id === activeReasoningId && m.kind === 'reasoning' ? { ...m, text: m.text + event.text } : m)
                  }
                  return [...msgs, { id: activeReasoningId, aiMessageId: activeAiTurnId, kind: 'reasoning', text: event.text }]
                })
                break
              case 'content':
                appendOrUpdate((msgs) => {
                  const existing = msgs.find(m => m.id === activeAssistantMsgId)
                  if (existing && existing.kind === 'assistant') {
                    return msgs.map(m => m.id === activeAssistantMsgId && m.kind === 'assistant' ? { ...m, content: m.content + event.text } : m)
                  }
                  return [...msgs, { id: activeAssistantMsgId, aiMessageId: activeAiTurnId, kind: 'assistant', content: event.text }]
                })
                break
              case 'metadata':
                appendOrUpdate((msgs) => {
                  return msgs.map(m => ('aiMessageId' in m && m.aiMessageId === activeAiTurnId) ? { ...m, metadata: { ...m.metadata, ...event.metadata } } as ChatUiMessage : m)
                })
                break
              case 'tool_call':
                appendOrUpdate((msgs) => [
                  ...msgs,
                  { id: `tc-${event.id}`, aiMessageId: activeAiTurnId, kind: 'tool_call', name: event.name, args: event.args }
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
}
