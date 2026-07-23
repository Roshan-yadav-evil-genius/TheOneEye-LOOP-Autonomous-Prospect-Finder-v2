import { ChatMessageList } from './chat-message-list'
import { ChatComposer } from './chat-composer'
import { Button } from '../../../shared/components/button'
import type { SetupChatStoreState } from '../stores/store-factory'

export interface SetupChatPanelProps {
  title: string
  threadId: string
  entityId: string
  agentDescription: string
  store: SetupChatStoreState
}

export function SetupChatPanel({ title, threadId, entityId, agentDescription, store }: SetupChatPanelProps) {
  const handleSend = (msg: string) => {
    void store.send(entityId, msg)
  }

  const handleClear = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      void store.clearHistory(entityId)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', flex: 1, minHeight: 0 }}>
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border-default)', paddingBottom: '14px', marginBottom: '14px', flexShrink: 0 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>{title}</h3>
          <p className="muted" style={{ margin: '4px 0 0 0', fontSize: '0.825rem' }}>
            {store.mode === 'chat' 
              ? `Thread: ${threadId}` 
              : `Agent: ${agentDescription}`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
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
                padding: '6px 14px',
                background: store.mode === 'chat' ? 'var(--color-accent-primary)' : 'transparent',
                color: store.mode === 'chat' ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.85rem',
                fontWeight: store.mode === 'chat' ? 700 : 'normal'
              }}
            >
              💬 Chat
            </button>
            <button
              type="button"
              onClick={() => store.setMode('agent')}
              style={{
                padding: '6px 14px',
                background: store.mode === 'agent' ? 'var(--color-accent-primary)' : 'transparent',
                color: store.mode === 'agent' ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.85rem',
                fontWeight: store.mode === 'agent' ? 700 : 'normal'
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
        <div style={{ background: 'var(--color-status-danger)', color: 'white', padding: '8px 12px', borderRadius: 'var(--radius-md)', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <span>{store.error}</span>
        </div>
      )}

      {/* Message List (Scrollable) */}
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <ChatMessageList messages={store.messages} streaming={store.streaming} />
      </div>
      
      {/* Input Composer (Pinned at Bottom) */}
      <div style={{ paddingTop: '12px', flexShrink: 0 }}>
        <ChatComposer 
          onSend={handleSend} 
          onContinue={() => store.retry(entityId)}
          disabled={store.streaming} 
          incompleteTurn={store.incompleteTurn}
          canResume={store.canResume}
        />
      </div>
    </div>
  )
}
