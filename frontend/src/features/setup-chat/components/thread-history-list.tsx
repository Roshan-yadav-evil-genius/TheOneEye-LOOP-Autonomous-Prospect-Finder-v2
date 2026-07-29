import type { SetupChatStoreState } from '../stores/store-factory'

export interface ThreadHistoryListProps {
  entityId: string
  store: SetupChatStoreState
}

function shortThreadId(id: string, maxLen = 40): string {
  if (id.length <= maxLen) return id
  return '…' + id.slice(-maxLen)
}

function getIconForThread(id: string) {
  let src = ''
  if (id.includes('strategy_setup_chat')) src = '/static/strategy_placeholder.png'
  else if (id.includes('product_setup_chat')) src = '/static/product_service_placeholder.png'
  else if (id.includes('org_setup_chat')) src = '/static/org_placeholder.png'
  
  if (src) {
    return <img src={src} alt="thread icon" style={{ width: '18px', height: '18px', borderRadius: '4px', objectFit: 'cover' }} />
  }
  return <span>🧵</span>
}

export function ThreadHistoryList({ entityId, store }: ThreadHistoryListProps) {
  const handleFetch = () => {
    void store.fetchThreads(entityId)
  }

  const handleSelect = (threadId: string) => {
    void store.selectThread(entityId, threadId)
  }

  const handleCopy = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    void navigator.clipboard.writeText(threadId)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <p className="muted" style={{ margin: 0, fontSize: '0.825rem' }}>
          Select a previous thread to resume it in chat.
        </p>
        <button
          type="button"
          onClick={handleFetch}
          disabled={store.loadingThreads}
          style={{
            padding: '5px 12px',
            background: 'var(--color-accent-primary)',
            color: 'var(--color-accent-foreground)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: store.loadingThreads ? 'not-allowed' : 'pointer',
            fontSize: '0.8rem',
            opacity: store.loadingThreads ? 0.6 : 1,
          }}
        >
          {store.loadingThreads ? 'Loading…' : '↺ Refresh'}
        </button>
      </div>

      {store.threadsList.length === 0 ? (
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          color: 'var(--color-text-muted)',
        }}>
          <span style={{ fontSize: '2rem' }}>📭</span>
          <p style={{ margin: 0, fontSize: '0.85rem' }}>
            {store.loadingThreads ? 'Fetching threads…' : 'No previous threads found. Click Refresh to load.'}
          </p>
        </div>
      ) : (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {store.threadsList.map((threadId) => {
            const isActive = threadId === store.activeThreadId
            return (
              <button
                key={threadId}
                type="button"
                onClick={() => handleSelect(threadId)}
                title={threadId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 14px',
                  background: isActive
                    ? 'var(--color-accent-primary)'
                    : 'var(--color-bg-elevated)',
                  color: isActive
                    ? 'var(--color-accent-foreground)'
                    : 'var(--color-text-primary)',
                  border: `1px solid ${isActive ? 'var(--color-accent-primary)' : 'var(--color-border-default)'}`,
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                  fontSize: '0.8rem',
                  fontFamily: 'monospace',
                  wordBreak: 'break-all',
                }}
              >
                <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px' }}>
                  {isActive ? <span style={{ fontSize: '0.95rem' }}>▶</span> : getIconForThread(threadId)}
                </span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  {shortThreadId(threadId)}
                </span>
                {isActive && (
                  <span style={{ flexShrink: 0, fontSize: '0.7rem', opacity: 0.85, marginRight: '8px' }}>
                    active
                  </span>
                )}
                <span
                  role="button"
                  title="Copy thread ID"
                  onClick={(e) => handleCopy(e, threadId)}
                  style={{
                    flexShrink: 0,
                    fontSize: '0.85rem',
                    cursor: 'copy',
                    opacity: 0.6,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    transition: 'opacity 0.2s, background 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '1'
                    e.currentTarget.style.background = isActive ? 'rgba(0,0,0,0.1)' : 'var(--color-bg-subtle)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '0.6'
                    e.currentTarget.style.background = 'transparent'
                  }}
                >
                  📋
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
