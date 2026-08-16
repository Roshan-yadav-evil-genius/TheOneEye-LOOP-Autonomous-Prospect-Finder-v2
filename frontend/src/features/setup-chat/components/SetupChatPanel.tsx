import { ChatMessageList } from './chat-message-list'
import { ChatComposer } from './chat-composer'
import { ThreadHistoryList } from './thread-history-list'
import { StateSnapshotList } from './state-snapshot-list'
import type { SetupChatStoreState } from '../stores/store-factory'

export interface SetupChatPanelProps {
  title: string
  threadId: string
  entityId: string
  agentDescription: string
  store: SetupChatStoreState
  noInputRequired?: boolean
}

type TabMode = 'ask' | 'state' | 'act' | 'history'

const tabs: { mode: TabMode; icon: string; label: string }[] = [
  { mode: 'ask', icon: '💬', label: 'Ask' },
  { mode: 'state', icon: '📊', label: 'State' },
  { mode: 'act', icon: '📝', label: 'Act' },
  { mode: 'history', icon: '📜', label: 'History' },
]

function TabButton({
  mode,
  icon,
  label,
  active,
  disabled,
  onClick,
}: {
  mode: TabMode
  icon: string
  label: string
  active: boolean
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      id={`setup-chat-tab-${mode}`}
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '6px 14px',
        background: active ? 'var(--color-accent-primary)' : 'transparent',
        color: active ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
        border: 'none',
        cursor: disabled ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '0.85rem',
        fontWeight: active ? 700 : 'normal',
      }}
    >
      {icon} {label}
    </button>
  )
}

export function SetupChatPanel({ title: _title, threadId: _threadId, entityId, agentDescription: _agentDescription, store, noInputRequired = false }: SetupChatPanelProps) {
  const handleSend = (msg: string) => {
    void store.send(entityId, msg)
  }

  const handleNewChat = () => {
    void store.createNewThread(entityId)
  }

  const handleTabClick = (mode: TabMode) => {
    if (mode === 'history' && store.mode !== 'history') {
      // Eagerly fetch threads when the tab is first opened
      void store.fetchThreads(entityId)
    }
    if (mode === 'state' && store.mode !== 'state') {
      void store.loadStateHistory(entityId)
    }
    store.setMode(mode)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', flex: 1, minHeight: 0 }}>
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border-default)', paddingBottom: '14px', marginBottom: '14px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img 
            src="/static/ChatBotAvatar.png" 
            alt="Masha" 
            style={{ width: '40px', height: '40px', borderRadius: '4px', objectFit: 'cover', border: '1px solid var(--color-border-default)' }} 
          />
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>Masha</h3>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {/* Tab switcher */}
          <div
            style={{
              display: 'flex',
              background: 'var(--color-bg-elevated)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border-default)',
              overflow: 'hidden',
              opacity: store.streaming ? 0.6 : 1,
              pointerEvents: store.streaming ? 'none' : 'auto',
            }}
          >
            {tabs.map(({ mode, icon, label }) => (
              <TabButton
                key={mode}
                mode={mode}
                icon={icon}
                label={label}
                active={store.mode === mode}
                disabled={store.streaming}
                onClick={() => handleTabClick(mode)}
              />
            ))}
            {store.mode !== 'history' && (
              <button
                type="button"
                id="setup-chat-new-thread-btn"
                onClick={handleNewChat}
                disabled={store.streaming || store.loadingThreads || store.messages.length === 0}
                title={store.messages.length === 0 ? 'Already in a new chat' : 'Start a new sequenced chat thread'}
                style={{
                  padding: '6px 14px',
                  background: 'transparent',
                  color: 'var(--color-text-primary)',
                  border: 'none',
                  borderLeft: '1px solid var(--color-border-default)',
                  cursor: store.streaming || store.loadingThreads || store.messages.length === 0 ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.85rem',
                  opacity: store.streaming || store.loadingThreads || store.messages.length === 0 ? 0.4 : 1,
                  transition: 'background 0.15s, opacity 0.15s',
                }}
                onMouseEnter={(e) => {
                  if (!e.currentTarget.disabled) e.currentTarget.style.background = 'var(--color-bg-subtle)'
                }}
                onMouseLeave={(e) => {
                  if (!e.currentTarget.disabled) e.currentTarget.style.background = 'transparent'
                }}
              >
                ➕ New
              </button>
            )}
          </div>
        </div>
      </div>


      {store.error && (
        <div style={{ background: 'var(--color-status-danger)', color: 'white', padding: '8px 12px', borderRadius: 'var(--radius-md)', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <span>{store.error}</span>
        </div>
      )}

      {/* Main content area */}
      {store.mode === 'history' ? (
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          <ThreadHistoryList entityId={entityId} store={store} />
        </div>
      ) : store.mode === 'state' ? (
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          <StateSnapshotList
            snapshots={store.stateSnapshots}
            loading={store.loadingSnapshots}
            onRefresh={() => void store.loadStateHistory(entityId)}
            onRetryCheckpoint={(config) => {
              void store.retry(entityId, config)
            }}
          />
        </div>
      ) : (
        <>
          {/* Message List (Scrollable) */}
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            <ChatMessageList
              messages={store.messages}
              streaming={store.streaming}
              onDeleteMessage={(messageId) => void store.deleteMessage(entityId, messageId)}
            />
          </div>

          {/* Input Composer (Pinned at Bottom) */}
          <div style={{ paddingTop: '12px', flexShrink: 0 }}>
            <ChatComposer
              onSend={handleSend}
              onContinue={() => store.retry(entityId)}
              disabled={store.streaming}
              incompleteTurn={store.incompleteTurn}
              canResume={store.canResume}
              noInputRequired={noInputRequired}
            />
          </div>
        </>
      )}
    </div>
  )
}

