import { useEffect, useRef, useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatUiMessage } from '../stores/store-factory'
import { ReasoningCard } from './reasoning-card'
import { ToolCallCard } from './tool-call-card'
import { ToolResultCard } from './tool-result-card'
import { TypingIndicator } from './typing-indicator'
import { getPublicToolCustomizations } from '../api/tool-customization-api'
import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { sharedMarkdownComponents, userMarkdownComponents, sharedRemarkPlugins } from './shared-markdown-components'
import { Modal } from '../../../shared/components/modal'
import { JsonHighlighter } from './json-highlighter'

function UserMessageBubble({ content }: { content: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [copied, setCopied] = useState(false)
  const isLong = content.length > 300

  const displayedContent = isLong && !isExpanded
    ? `${content.slice(0, 300)}...`
    : content

  const handleCopy = () => {
    if (navigator.clipboard && content) {
      void navigator.clipboard.writeText(content).then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }).catch(console.error)
    }
  }

  return (
    <div style={{ background: 'var(--color-accent-primary)', color: 'var(--color-accent-foreground)', padding: '10px 14px', borderRadius: '16px 16px 0 16px', maxWidth: '85%', wordBreak: 'break-word' }}>
      <ReactMarkdown remarkPlugins={sharedRemarkPlugins} components={userMarkdownComponents as any}>
        {displayedContent}
      </ReactMarkdown>
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px', marginTop: '8px', paddingTop: '6px', borderTop: '1px solid rgba(0, 0, 0, 0.1)' }}>
        {isLong && (
          <button
            type="button"
            onClick={() => setIsExpanded(prev => !prev)}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              color: '#0f172a',
              border: '1px solid rgba(0, 0, 0, 0.12)',
              borderRadius: '6px',
              fontSize: '0.78rem',
              fontWeight: 600,
              padding: '4px 10px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 1px 2px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.15s ease'
            }}
          >
            <span>{isExpanded ? 'Show less' : 'Show more'}</span>
            <span style={{ fontSize: '0.7rem' }}>{isExpanded ? '🔼' : '🔽'}</span>
          </button>
        )}
        <button
          type="button"
          onClick={handleCopy}
          title="Copy message"
          style={{
            background: copied ? '#15803d' : 'rgba(255, 255, 255, 0.9)',
            color: copied ? '#ffffff' : '#0f172a',
            border: `1px solid ${copied ? '#15803d' : 'rgba(0, 0, 0, 0.12)'}`,
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontWeight: 600,
            padding: '4px 10px',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.08)',
            transition: 'all 0.15s ease'
          }}
        >
          <span style={{ fontSize: '0.85rem' }}>{copied ? '✓' : '📋'}</span>
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
    </div>
  )
}

function AssistantMessageBubble({ content }: { content: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    if (navigator.clipboard && content) {
      void navigator.clipboard.writeText(content).then(() => {
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }).catch(console.error)
    }
  }

  return (
    <div className="markdown-chat" style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-text-primary)', padding: '10px 16px', borderRadius: '16px 16px 16px 0', width: '100%', wordBreak: 'break-word', border: '1px solid var(--color-border-default)', position: 'relative' }}>
      <ReactMarkdown remarkPlugins={sharedRemarkPlugins} components={sharedMarkdownComponents as any}>
        {content}
      </ReactMarkdown>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--color-border-default)' }}>
        <button
          type="button"
          onClick={handleCopy}
          title="Copy response"
          style={{
            background: copied ? 'rgba(34, 197, 94, 0.18)' : 'var(--color-bg-subtle, rgba(255, 255, 255, 0.05))',
            color: copied ? '#4ade80' : 'var(--color-text-secondary)',
            border: `1px solid ${copied ? 'rgba(34, 197, 94, 0.4)' : 'var(--color-border-default)'}`,
            borderRadius: '6px',
            fontSize: '0.78rem',
            fontWeight: 600,
            padding: '4px 10px',
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            fontFamily: 'inherit',
            transition: 'all 0.15s ease'
          }}
        >
          <span style={{ fontSize: '0.85rem' }}>{copied ? '✓' : '📋'}</span>
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
    </div>
  )
}

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
                <UserMessageBubble content={msg.content} />
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
            <div key={group.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%', gap: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '4px' }}>
                <img 
                  src="/static/ChatBotAvatar.png" 
                  alt="Masha" 
                  style={{ width: '24px', height: '24px', borderRadius: '4px', objectFit: 'cover' }} 
                />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Masha</span>
              </div>
              <div style={{ 
                width: '100%', 
                maxWidth: '85%', 
                borderLeft: '3px solid #eab308', 
                paddingLeft: '12px', 
                marginLeft: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                {group.messages.map(msg => (
                  <div key={msg.id}>
                    {msg.kind === 'assistant' && msg.content && (
                      <AssistantMessageBubble content={msg.content} />
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
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '4px' }}>
            <img 
              src="/static/ChatBotAvatar.png" 
              alt="Masha" 
              style={{ width: '24px', height: '24px', borderRadius: '4px', objectFit: 'cover' }} 
            />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Masha</span>
          </div>
          <div style={{ marginLeft: '14px', paddingLeft: '12px', borderLeft: '3px solid #eab308' }}>
            <TypingIndicator />
          </div>
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
