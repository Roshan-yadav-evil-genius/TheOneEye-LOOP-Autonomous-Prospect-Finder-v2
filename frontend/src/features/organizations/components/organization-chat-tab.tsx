import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useOrganizationChatStore } from '../stores/organization-chat-store'
import { ChatMessageList } from './chat/chat-message-list'
import { ChatComposer } from './chat/chat-composer'
import { Button } from '../../../shared/components/button'

export function OrganizationChatTab() {
  const { orgId = '' } = useParams()
  const store = useOrganizationChatStore()

  const { loadHistory, reset } = store

  useEffect(() => {
    void loadHistory(orgId)
    return () => reset()
  }, [orgId, loadHistory, reset])

  const handleSend = (msg: string) => {
    void store.send(orgId, msg)
  }

  const handleClear = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      void store.clearHistory(orgId)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '600px', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border-default)', paddingBottom: '12px', marginBottom: '12px' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Organization Setup Assistant</h3>
          <p className="muted" style={{ margin: '4px 0 0 0', fontSize: '0.85rem' }}>
            {store.mode === 'chat' 
              ? `Thread: org_${orgId}_setup_chat` 
              : 'Agent: can update organization profile; switch to Details tab to see saved fields'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div 
            style={{ 
              display: 'flex', 
              background: 'var(--color-bg-elevated)', 
              borderRadius: 'var(--radius-md)', 
              border: '1px solid var(--color-border-default)', 
              overflow: 'hidden',
              opacity: store.streaming ? 0.6 : 1,
              pointerEvents: store.streaming ? 'none' : 'auto'
            }}
          >
            <button
              type="button"
              onClick={() => store.setMode('chat')}
              style={{
                padding: '6px 12px',
                background: store.mode === 'chat' ? 'var(--color-accent-primary)' : 'transparent',
                color: store.mode === 'chat' ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: store.mode === 'chat' ? 500 : 'normal'
              }}
            >
              💬 Chat
            </button>
            <button
              type="button"
              onClick={() => store.setMode('agent')}
              style={{
                padding: '6px 12px',
                background: store.mode === 'agent' ? 'var(--color-accent-primary)' : 'transparent',
                color: store.mode === 'agent' ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: store.mode === 'agent' ? 500 : 'normal'
              }}
            >
              📝 Agent
            </button>
          </div>
          <Button type="button" variant="ghost" onClick={handleClear} disabled={store.streaming}>
            Clear
          </Button>
        </div>
      </div>
      
      {store.error && (
        <div style={{ background: 'var(--color-status-danger)', color: 'var(--color-text-primary)', padding: '8px 12px', borderRadius: 'var(--radius-md)', marginBottom: '12px' }}>
          {store.error}
        </div>
      )}

      <ChatMessageList messages={store.messages} streaming={store.streaming} />
      
      <ChatComposer onSend={handleSend} disabled={store.streaming} />
    </div>
  )
}
