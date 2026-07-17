import { useEffect, useRef, useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatUiMessage } from '../stores/store-factory'
import { ReasoningCard } from './reasoning-card'
import { ToolCallCard } from './tool-call-card'
import { ToolResultCard } from './tool-result-card'
import { TypingIndicator } from './typing-indicator'
import { getPublicToolCustomizations } from '../api/tool-customization-api'
import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { sharedMarkdownComponents, userMarkdownComponents } from './shared-markdown-components'
import { Modal } from '../../../shared/components/modal'
import { JsonHighlighter } from './json-highlighter'

export function ChatMessageList({ messages, streaming, emptyMessage }: { messages: ChatUiMessage[], streaming?: boolean, emptyMessage?: string }) {
  const endRef = useRef<HTMLDivElement>(null)
  const [rules, setRules] = useState<ToolCustomizationRuleRead[]>([])
  const [inspectJson, setInspectJson] = useState<any>(null)

  const renderMetadata = (metadata?: Record<string, any>) => {
    if (!metadata || Object.keys(metadata).length === 0) return null
    
    const modelName = metadata.response_metadata?.model || metadata.response_metadata?.model_name
    const createdAt = metadata.response_metadata?.created_at || metadata.created_at
    const displayId = metadata.id
    
    return (
      <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '0.75em', color: 'var(--color-text-secondary)', padding: '0 4px' }}>
        {metadata.raw && (
          <button 
            type="button" 
            onClick={() => setInspectJson(metadata.raw)}
            title="Inspect raw response"
            style={{ 
              background: 'none', border: 'none', padding: 0, cursor: 'pointer', 
              color: 'var(--color-text-secondary)', fontSize: 'inherit',
              display: 'flex', alignItems: 'center', gap: '4px',
              fontFamily: 'inherit'
            }}
          >
            <span style={{ opacity: 0.8 }}>🔍</span>
            <span style={{ textDecoration: 'underline', textDecorationColor: 'var(--color-border-default)' }}>Inspect</span>
          </button>
        )}
        {modelName && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Model">
            <span>🧠</span>
            <span>{modelName}</span>
          </div>
        )}
        {metadata.usage_metadata && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title={`Input: ${metadata.usage_metadata.input_tokens}, Output: ${metadata.usage_metadata.output_tokens}`}>
            <span>🪙</span>
            <span>{metadata.usage_metadata.total_tokens?.toLocaleString() || (metadata.usage_metadata.input_tokens + metadata.usage_metadata.output_tokens).toLocaleString()} tokens</span>
          </div>
        )}
        {createdAt && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Date & Time">
            <span>📅</span>
            <span>{new Date(createdAt).toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          </div>
        )}
        {metadata.response_metadata?.eval_duration && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Evaluation duration">
            <span>⏱️</span>
            <span>{(metadata.response_metadata.eval_duration / 1e9).toFixed(2)}s</span>
          </div>
        )}
        {displayId && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', opacity: 0.6 }} title={`Run ID: ${metadata.id}`}>
            <span>🆔</span>
            <span style={{ fontFamily: 'monospace' }}>{displayId}</span>
          </div>
        )}
      </div>
    )
  }

  useEffect(() => {
    void getPublicToolCustomizations().then(setRules).catch(console.error)
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const groupedMessages = useMemo(() => {
    const groups: { id: string; kind: 'user' | 'ai' | 'tool_result'; messages: ChatUiMessage[]; aiMessageId?: string }[] = []
    
    messages.forEach((msg) => {
      const isAiMsg = msg.kind === 'assistant' || msg.kind === 'reasoning' || msg.kind === 'tool_call'
      const aiMessageId = isAiMsg ? (msg as any).aiMessageId : undefined
      
      const lastGroup = groups[groups.length - 1]
      
      if (msg.kind === 'user') {
        groups.push({ id: msg.id, kind: 'user', messages: [msg] })
      } else if (msg.kind === 'tool_result') {
        groups.push({ id: msg.id, kind: 'tool_result', messages: [msg] })
      } else if (isAiMsg) {
        if (lastGroup && lastGroup.kind === 'ai' && lastGroup.aiMessageId === aiMessageId) {
          lastGroup.messages.push(msg)
        } else {
          groups.push({ id: msg.id, kind: 'ai', messages: [msg], aiMessageId })
        }
      }
    })
    
    return groups
  }, [messages])

  return (
    <div className="chat-message-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, overflowY: 'auto', padding: '16px 4px' }}>
      {messages.length === 0 ? (
        <p className="muted" style={{ textAlign: 'center', margin: 'auto' }}>{emptyMessage || 'No messages yet. Say hello!'}</p>
      ) : (
        groupedMessages.map((group) => {
          if (group.kind === 'user') {
            const msg = group.messages[0]
            if (msg.kind !== 'user') return null
            return (
              <div key={group.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', width: '100%' }}>
                <div style={{ background: 'var(--color-accent-primary)', color: 'var(--color-accent-foreground)', padding: '8px 12px', borderRadius: '16px 16px 0 16px', maxWidth: '85%', wordBreak: 'break-word' }}>
                  <ReactMarkdown components={userMarkdownComponents as any}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            )
          }

          if (group.kind === 'tool_result') {
            const msg = group.messages[0]
            if (msg.kind !== 'tool_result') return null
            return (
              <div key={group.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
                <div style={{ width: '100%', maxWidth: '85%' }}>
                   <ToolResultCard name={msg.name} content={msg.content} rules={rules} />
                </div>
              </div>
            )
          }

          // AI Group
          const metadata = group.messages.length > 0 ? (group.messages[group.messages.length - 1] as any).metadata : undefined
          return (
            <div key={group.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
              <div style={{ 
                width: '100%', 
                maxWidth: '85%', 
                borderLeft: '3px solid #eab308', 
                paddingLeft: '12px', 
                marginLeft: '4px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {group.messages.map(msg => (
                  <div key={msg.id}>
                    {msg.kind === 'assistant' && msg.content && (
                      <div className="markdown-chat" style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-text-primary)', padding: '8px 16px', borderRadius: '16px 16px 16px 0', width: '100%', wordBreak: 'break-word', border: '1px solid var(--color-border-default)' }}>
                        <ReactMarkdown components={sharedMarkdownComponents as any}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
                    {msg.kind === 'reasoning' && <ReasoningCard text={msg.text} />}
                    {msg.kind === 'tool_call' && <ToolCallCard name={msg.name} args={msg.args} rules={rules} />}
                  </div>
                ))}
                
                {metadata && (
                  <div style={{ marginTop: '4px' }}>
                    {renderMetadata(metadata)}
                  </div>
                )}
              </div>
            </div>
          )
        })
      )}
      {streaming && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
          <TypingIndicator />
        </div>
      )}
      <div ref={endRef} />
      
      <Modal 
        open={!!inspectJson} 
        onOpenChange={(open) => { if (!open) setInspectJson(null) }} 
        title="Raw AI Response"
        contentStyle={{ maxWidth: '900px', width: '90vw' }}
      >
        <div style={{ maxHeight: '70vh', overflowY: 'auto', borderRadius: '6px' }}>
          {inspectJson && <JsonHighlighter data={inspectJson} />}
        </div>
      </Modal>
    </div>
  )
}
