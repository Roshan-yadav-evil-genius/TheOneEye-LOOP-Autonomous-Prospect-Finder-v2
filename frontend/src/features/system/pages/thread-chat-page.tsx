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
        res.data.messages.forEach((m, i) => {
          if (m.role === 'tool_call') {
            uiMessages.push({ id: `hist-${i}`, kind: 'tool_call', name: m.name || '', args: m.args || {} })
          } else if (m.role === 'tool_result') {
            uiMessages.push({ id: `hist-${i}`, kind: 'tool_result', name: m.name || '', content: m.content })
          } else if (m.role === 'reasoning') {
            uiMessages.push({ id: `hist-${i}`, kind: 'reasoning', text: m.content })
          } else if (m.role === 'user') {
            const lastMsg = uiMessages[uiMessages.length - 1]
            if (lastMsg && lastMsg.kind === 'user' && lastMsg.content === m.content) {
              return
            }
            uiMessages.push({ id: `hist-${i}`, kind: 'user', content: m.content })
          } else {
            uiMessages.push({ id: `hist-${i}`, kind: 'assistant', content: m.content })
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
