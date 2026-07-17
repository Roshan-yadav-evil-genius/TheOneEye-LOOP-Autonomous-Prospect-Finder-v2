import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

import { apiClient } from '../../../shared/api/client'
import { Button } from '../../../shared/components/button'
import { PageHeader } from '../../../shared/components/page-header'
import type { ChatHistoryRead } from '../../setup-chat/api/setup-chat-api-client'
import { ChatMessageList } from '../../setup-chat/components/chat-message-list'
import type { ChatUiMessage } from '../../setup-chat/stores/store-factory'

export function ThreadChatPage() {
  const { threadId } = useParams()
  const navigate = useNavigate()

  const [messages, setMessages] = useState<ChatUiMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    if (!threadId) return

    setLoading(true)
    setError(null)

    apiClient.get<ChatHistoryRead>(`/api/v1/threads/${encodeURIComponent(threadId)}/chat/history`)
      .then((res) => {
        if (!mounted) return

        const uiMessages: ChatUiMessage[] = []
        res.data.messages.forEach((msgDict: any, i: number) => {
          const type = msgDict.type
          const data = msgDict.data || {}
          
          if (type === 'human') {
            const content = typeof data.content === 'string' ? data.content : JSON.stringify(data.content)
            const lastMsg = uiMessages[uiMessages.length - 1]
            if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === content) {
              return
            }
            uiMessages.push({ id: `hist-${i}`, kind: 'user', content })
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
              uiMessages.push({ id: `hist-${i}-rsn`, aiMessageId, kind: 'reasoning', text: reasoning, metadata: metadataObj })
            }
            
            if (contentStr && contentStr !== '""' && contentStr !== '[]' && contentStr !== '"[]"') {
              uiMessages.push({ id: `hist-${i}-ast`, aiMessageId, kind: 'assistant', content: contentStr, metadata: metadataObj })
            }
            
            toolCalls.forEach((tc: any, tcIdx: number) => {
              uiMessages.push({ id: `hist-${i}-tc-${tcIdx}`, aiMessageId, kind: 'tool_call', name: tc.name, args: tc.args, metadata: metadataObj })
            })
            
            if (!reasoning && (!contentStr || contentStr === '""' || contentStr === '[]' || contentStr === '"[]"') && toolCalls.length === 0) {
              uiMessages.push({ id: `hist-${i}-ast`, aiMessageId, kind: 'assistant', content: '', metadata: metadataObj })
            }
          } else if (type === 'tool') {
            uiMessages.push({ id: `hist-${i}-tr`, kind: 'tool_result', name: data.name, content: typeof data.content === 'string' ? data.content : JSON.stringify(data.content) })
          }
        })

        setMessages(uiMessages)
        setLoading(false)
      })
      .catch((err) => {
        if (!mounted) return
        setError(err.message || 'Failed to load thread history')
        setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [threadId])

  return (
    <div className="workspace-shell" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <PageHeader
        title="Thread Chat"
        subtitle={threadId ? `Thread ID: ${threadId}` : ''}
        actions={
          <Button variant="outline" onClick={() => navigate(-1)}>
            Back
          </Button>
        }
      />
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: '0 2rem 2rem 2rem' }}>
        {loading ? (
          <p className="muted">Loading chat...</p>
        ) : error ? (
          <p style={{ color: 'var(--color-danger)' }}>{error}</p>
        ) : (
          <div style={{ flex: 1, background: 'var(--color-bg-subtle)', borderRadius: '8px', border: '1px solid var(--color-border-default)', overflow: 'hidden', display: 'flex' }}>
            <ChatMessageList messages={messages} emptyMessage="No chat history for this thread." />
          </div>
        )}
      </div>
    </div>
  )
}
