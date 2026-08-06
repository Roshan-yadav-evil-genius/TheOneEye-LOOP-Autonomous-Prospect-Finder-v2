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

  const handleSelect = (threadId: string, ns: string | null = null) => {
    void store.selectThread(entityId, threadId, ns)
  }

  const handleCopy = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    void navigator.clipboard.writeText(threadId)
  }

  const handleDelete = (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    if (window.confirm(`Delete thread: ${threadId}?`)) {
      void store.deleteThread(entityId, threadId)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <p className="muted" style={{ margin: 0, fontSize: '0.825rem' }}>
          Select a thread or subagent namespace to load chat.
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
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {store.threadsList.map((threadId) => {
            const isThreadActive = threadId === store.activeThreadId
            const namespaces = store.namespacesMap[threadId] || []
            const currentNs = isThreadActive ? store.activeNamespace : null

            return (
              <div
                key={threadId}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  padding: '10px',
                  background: isThreadActive
                    ? 'var(--color-bg-elevated)'
                    : 'var(--color-bg-subtle)',
                  border: `1px solid ${isThreadActive ? 'var(--color-accent-primary)' : 'var(--color-border-default)'}`,
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px' }}>
                    {isThreadActive && currentNs === null ? <span style={{ fontSize: '0.95rem' }}>▶</span> : getIconForThread(threadId)}
                  </span>
                  <span
                    onClick={() => handleSelect(threadId, null)}
                    title={threadId}
                    style={{
                      flex: 1,
                      minWidth: 0,
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      fontFamily: 'monospace',
                      fontWeight: isThreadActive && currentNs === null ? 'bold' : 'normal',
                      wordBreak: 'break-all',
                    }}
                  >
                    {shortThreadId(threadId)}
                  </span>
                  {isThreadActive && currentNs === null && (
                    <span style={{ flexShrink: 0, fontSize: '0.7rem', opacity: 0.85, marginRight: '4px' }}>
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
                    }}
                  >
                    📋
                  </span>
                  <span
                    role="button"
                    title="Delete thread"
                    onClick={(e) => handleDelete(e, threadId)}
                    style={{
                      flexShrink: 0,
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      opacity: 0.6,
                      padding: '2px 6px',
                      borderRadius: '4px',
                    }}
                  >
                    🗑️
                  </span>
                </div>

                {namespaces.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', paddingLeft: '30px', marginTop: '2px' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', width: '100%', marginBottom: '2px' }}>
                      Subagent Namespaces:
                    </span>
                    <button
                      type="button"
                      onClick={() => handleSelect(threadId, null)}
                      style={{
                        padding: '2px 8px',
                        fontSize: '0.725rem',
                        borderRadius: '12px',
                        border: '1px solid var(--color-border-default)',
                        background: isThreadActive && currentNs === null ? 'var(--color-accent-primary)' : 'var(--color-bg-elevated)',
                        color: isThreadActive && currentNs === null ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                        cursor: 'pointer',
                      }}
                    >
                      [Main Graph]
                    </button>
                    {namespaces.map((ns) => {
                      if (!ns) return null
                      const isNsActive = isThreadActive && currentNs === ns
                      return (
                        <button
                          key={ns}
                          type="button"
                          onClick={() => handleSelect(threadId, ns)}
                          title={`View namespace chat: ${ns}`}
                          style={{
                            padding: '2px 8px',
                            fontSize: '0.725rem',
                            borderRadius: '12px',
                            border: `1px solid ${isNsActive ? 'var(--color-accent-primary)' : 'var(--color-border-default)'}`,
                            background: isNsActive ? 'var(--color-accent-primary)' : 'var(--color-bg-elevated)',
                            color: isNsActive ? 'var(--color-accent-foreground)' : 'var(--color-text-primary)',
                            cursor: 'pointer',
                            fontFamily: 'monospace',
                          }}
                        >
                          📦 {ns}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
