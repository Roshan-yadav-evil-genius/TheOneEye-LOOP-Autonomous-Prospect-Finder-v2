import { create, type StoreApi, type UseBoundStore } from 'zustand'

import {
  type ChatStreamEvent,
  type ChatStreamRequest,
  type ChatHistoryRead,
  type StateSnapshotRead
} from '../api/setup-chat-api-client'

export type ChatUiMessage =
  | { id: string; messageId?: string; kind: 'user'; content: string }
  | { id: string; messageId?: string; aiMessageId?: string; kind: 'assistant'; content: string; metadata?: Record<string, any> }
  | { id: string; messageId?: string; aiMessageId?: string; kind: 'reasoning'; text: string; metadata?: Record<string, any> }
  | { id: string; messageId?: string; aiMessageId?: string; kind: 'tool_call'; name: string; args: unknown; metadata?: Record<string, any> }
  | { id: string; messageId?: string; kind: 'tool_result'; name: string; content: string }

export interface SetupChatStoreState {
  mode: 'chat' | 'state' | 'agent' | 'history'
  messages: ChatUiMessage[]
  stateSnapshots: StateSnapshotRead[]
  loadingSnapshots: boolean
  streaming: boolean
  error: string | null
  profileDirtyFromChat: boolean
  
  incompleteTurn: boolean
  canResume: boolean
  lastUserMessage: string | null

  /** Thread & Namespace state */
  threadsList: string[]
  activeThreadId: string | null
  activeNamespace: string | null
  namespacesMap: Record<string, string[]>
  loadingThreads: boolean
  
  setMode: (mode: 'chat' | 'state' | 'agent' | 'history') => void
  loadHistory: (entityId: string, threadId?: string | null, checkpoint_ns?: string | null) => Promise<void>
  loadStateHistory: (entityId: string, threadId?: string | null, checkpoint_ns?: string | null) => Promise<void>
  clearHistory: (entityId: string) => Promise<void>
  deleteMessage: (entityId: string, messageId: string) => Promise<void>
  send: (entityId: string, message: string) => Promise<void>
  retry: (entityId: string) => Promise<void>
  reset: () => void
  clearDirtyFlag: () => void
  fetchThreads: (entityId: string) => Promise<void>
  selectThread: (entityId: string, threadId: string, checkpoint_ns?: string | null) => Promise<void>
  createNewThread: (entityId: string) => Promise<void>
  deleteThread: (entityId: string, threadId: string) => Promise<void>
  
  _runStream: (entityId: string, request: ChatStreamRequest) => Promise<void>
}

export interface SetupChatApi {
  getHistory: (entityId: string, threadId?: string | null, checkpoint_ns?: string | null) => Promise<ChatHistoryRead>
  getStateHistory?: (entityId: string, threadId?: string | null, checkpoint_ns?: string | null) => Promise<StateSnapshotRead[]>
  clearChat: (entityId: string, threadId?: string | null) => Promise<any>
  deleteMessage?: (entityId: string, messageId: string, threadId?: string | null) => Promise<any>
  streamChat: (entityId: string, request: ChatStreamRequest, onEvent: (event: ChatStreamEvent) => void) => Promise<void>
  getThreads?: (entityId: string) => Promise<string[] | { threads: string[]; namespaces?: Record<string, string[]> }>
  newThread?: (entityId: string) => Promise<{ thread_id: string }>
}

export function createSetupChatStore(api: SetupChatApi, storageKey = 'setup_chat_mode'): UseBoundStore<StoreApi<SetupChatStoreState>> {
  const getInitialMode = (): 'chat' | 'agent' => {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const saved = window.localStorage.getItem(storageKey)
        if (saved === 'agent' || saved === 'chat') {
          return saved
        }
      }
    } catch {
      // Ignore storage errors
    }
    return 'chat'
  }

  return create<SetupChatStoreState>((set, get) => ({
    mode: (getInitialMode() as 'chat' | 'state' | 'agent' | 'history') || 'chat',
    messages: [],
    stateSnapshots: [],
    loadingSnapshots: false,
    streaming: false,
    error: null,
    profileDirtyFromChat: false,
    incompleteTurn: false,
    canResume: false,
    lastUserMessage: null,
    threadsList: [],
    activeThreadId: null,
    activeNamespace: null,
    namespacesMap: {},
    loadingThreads: false,

    setMode: (mode) => {
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          window.localStorage.setItem(storageKey, mode)
        }
      } catch {
        // Ignore storage errors
      }
      set({ mode })
    },

    reset: () => set({ 
      messages: [], 
      stateSnapshots: [],
      loadingSnapshots: false,
      streaming: false, 
      error: null, 
      profileDirtyFromChat: false,
      incompleteTurn: false,
      canResume: false,
      lastUserMessage: null,
      threadsList: [],
      activeThreadId: null,
      activeNamespace: null,
      namespacesMap: {},
      loadingThreads: false,
    }),
    
    clearDirtyFlag: () => set({ profileDirtyFromChat: false }),

    fetchThreads: async (entityId) => {
      if (!api.getThreads) return
      try {
        set({ loadingThreads: true, error: null })
        const res = await api.getThreads(entityId)
        if (Array.isArray(res)) {
          set({ threadsList: res, namespacesMap: {} })
        } else {
          set({ threadsList: res.threads || [], namespacesMap: res.namespaces || {} })
        }
      } catch (e: any) {
        set({ error: e.message || 'Failed to load threads' })
      } finally {
        set({ loadingThreads: false })
      }
    },

    loadStateHistory: async (entityId, threadId, checkpoint_ns) => {
      if (!api.getStateHistory) return
      try {
        set({ loadingSnapshots: true, error: null })
        const targetThreadId = threadId ?? get().activeThreadId
        const targetNs = checkpoint_ns !== undefined ? checkpoint_ns : get().activeNamespace
        const snapshots = await api.getStateHistory(entityId, targetThreadId, targetNs)
        set({ stateSnapshots: snapshots || [] })
      } catch (e: any) {
        set({ error: e.message || 'Failed to load state history' })
      } finally {
        set({ loadingSnapshots: false })
      }
    },

    selectThread: async (entityId, threadId, checkpoint_ns = null) => {
      set({ activeThreadId: threadId, activeNamespace: checkpoint_ns, mode: 'chat' })
      await Promise.all([
        get().loadHistory(entityId, threadId, checkpoint_ns),
        get().loadStateHistory(entityId, threadId, checkpoint_ns),
      ])
    },

    createNewThread: async (entityId) => {
      if (!api.newThread) return
      try {
        set({ error: null, loadingThreads: true })
        const { thread_id } = await api.newThread(entityId)
        set({
          activeThreadId: thread_id,
          activeNamespace: null,
          messages: [],
          mode: 'chat',
          incompleteTurn: false,
          canResume: false,
          lastUserMessage: null,
        })
      } catch (e: any) {
        set({ error: e.message || 'Failed to create new thread' })
      } finally {
        set({ loadingThreads: false })
      }
    },

    deleteThread: async (entityId, threadId) => {
      try {
        set({ error: null })
        await api.clearChat(entityId, threadId)
        const updatedList = get().threadsList.filter((t) => t !== threadId)
        set({ threadsList: updatedList })
        if (get().activeThreadId === threadId) {
          if (updatedList.length > 0) {
            await get().selectThread(entityId, updatedList[0])
          } else {
            set({
              activeThreadId: null,
              activeNamespace: null,
              messages: [],
              incompleteTurn: false,
              canResume: false,
              lastUserMessage: null,
            })
          }
        }
      } catch (e: any) {
        set({ error: e.message || 'Failed to delete thread' })
      }
    },

    loadHistory: async (entityId, threadId, checkpoint_ns) => {
      try {
        set({ error: null })
        const targetThreadId = threadId ?? get().activeThreadId
        const targetNs = checkpoint_ns !== undefined ? checkpoint_ns : get().activeNamespace
        const history = await api.getHistory(entityId, targetThreadId, targetNs)
        
        const messages: ChatUiMessage[] = []
        let lastUserMsg: string | null = null
        
        history.messages.forEach((msgDict: any, i: number) => {
          const type = msgDict.type
          const data = msgDict.data || {}
          const rawMessageId = msgDict.id || data.id
          
          if (type === 'human') {
            const content = typeof data.content === 'string' ? data.content : JSON.stringify(data.content)
            lastUserMsg = content
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === content) {
              return
            }
            messages.push({ id: `hist-${i}`, messageId: rawMessageId, kind: 'user', content })
          } else if (type === 'ai') {
            const aiMessageId = rawMessageId || `hist-${i}`
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
              messages.push({ id: `hist-${i}-rsn`, messageId: aiMessageId, aiMessageId, kind: 'reasoning', text: reasoning, metadata: metadataObj })
            }
            
            if (contentStr && contentStr !== '""' && contentStr !== '[]' && contentStr !== '"[]"') {
              messages.push({ id: `hist-${i}-ast`, messageId: aiMessageId, aiMessageId, kind: 'assistant', content: contentStr, metadata: metadataObj })
            }
            
            toolCalls.forEach((tc: any, tcIdx: number) => {
              messages.push({ id: `hist-${i}-tc-${tcIdx}`, messageId: aiMessageId, aiMessageId, kind: 'tool_call', name: tc.name, args: tc.args, metadata: metadataObj })
            })
            
            if (!reasoning && (!contentStr || contentStr === '""' || contentStr === '[]' || contentStr === '"[]"') && toolCalls.length === 0) {
              messages.push({ id: `hist-${i}-ast`, messageId: aiMessageId, aiMessageId, kind: 'assistant', content: '', metadata: metadataObj })
            }
          } else if (type === 'tool') {
            messages.push({ id: `hist-${i}-tr`, messageId: rawMessageId, kind: 'tool_result', name: data.name, content: typeof data.content === 'string' ? data.content : JSON.stringify(data.content) })
          }
        })
        
        set({ 
          messages, 
          activeThreadId: targetThreadId ?? get().activeThreadId,
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

    deleteMessage: async (entityId: string, messageId: string) => {
      if (!api.deleteMessage) return
      try {
        set({ error: null })
        await api.deleteMessage(entityId, messageId, get().activeThreadId)
        set({
          messages: get().messages.filter(
            (m) =>
              m.id !== messageId &&
              (m as any).messageId !== messageId &&
              ('aiMessageId' in m && m.aiMessageId ? m.aiMessageId !== messageId : true)
          ),
        })
      } catch (e: any) {
        set({ error: e.message || 'Failed to delete message' })
      }
    },

    send: async (entityId, message) => {
      const { mode, messages, activeThreadId } = get()
      
      const newMessages = message.trim() 
        ? [...messages, { id: `user-${Date.now()}`, kind: 'user', content: message } as ChatUiMessage]
        : messages

      set({ messages: newMessages, streaming: true, error: null, lastUserMessage: message || null })

      const modeArg = mode === 'history' ? 'chat' : mode
      await get()._runStream(entityId, { message, mode: modeArg, thread_id: activeThreadId })
    },
    
    retry: async (entityId: string) => {
      const { mode, canResume, lastUserMessage, activeThreadId } = get()
      set({ streaming: true, error: null })
      
      const redo_last = !canResume
      const message = (redo_last && lastUserMessage) ? lastUserMessage : ''
      
      const modeArg = mode === 'history' ? 'chat' : mode
      await get()._runStream(entityId, { message, mode: modeArg, retry: true, redo_last, thread_id: activeThreadId })
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
