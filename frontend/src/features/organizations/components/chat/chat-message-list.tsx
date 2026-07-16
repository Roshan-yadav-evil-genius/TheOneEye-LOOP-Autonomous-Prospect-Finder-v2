import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatUiMessage } from '../../stores/organization-chat-store'
import { ReasoningCard } from './reasoning-card'
import { ToolCallCard } from './tool-call-card'
import { ToolResultCard } from './tool-result-card'
import { TypingIndicator } from './typing-indicator'

export function ChatMessageList({ messages, streaming }: { messages: ChatUiMessage[], streaming?: boolean }) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-message-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflowY: 'auto', padding: '16px 4px' }}>
      {messages.length === 0 ? (
        <p className="muted" style={{ textAlign: 'center', margin: 'auto' }}>No messages yet. Say hello!</p>
      ) : (
        messages.map((msg) => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.kind === 'user' ? 'flex-end' : 'flex-start', width: '100%' }}>
            {msg.kind === 'user' && (
              <div style={{ background: 'var(--color-accent-primary)', color: 'var(--color-accent-foreground)', padding: '8px 12px', borderRadius: '16px 16px 0 16px', maxWidth: '85%', wordBreak: 'break-word' }}>
                {msg.content}
              </div>
            )}
            {msg.kind === 'assistant' && (
              <div className="markdown-chat" style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-text-primary)', padding: '8px 16px', borderRadius: '16px 16px 16px 0', maxWidth: '85%', wordBreak: 'break-word', border: '1px solid var(--color-border-default)' }}>
                <ReactMarkdown components={{
                  p: ({node, ...props}) => <p style={{margin: '0 0 8px 0'}} {...props} />,
                  ul: ({node, ...props}) => <ul style={{margin: '0 0 8px 24px', padding: 0, listStyleType: 'disc'}} {...props} />,
                  ol: ({node, ...props}) => <ol style={{margin: '0 0 8px 24px', padding: 0, listStyleType: 'decimal'}} {...props} />,
                  li: ({node, ...props}) => <li style={{margin: '4px 0'}} {...props} />,
                  a: ({node, ...props}) => <a style={{color: 'var(--color-accent-primary)', textDecoration: 'underline'}} target="_blank" rel="noopener noreferrer" {...props} />
                }}>
                  {msg.content}
                </ReactMarkdown>
              </div>
            )}
            {msg.kind === 'reasoning' && <ReasoningCard text={msg.text} />}
            {msg.kind === 'tool_call' && <ToolCallCard name={msg.name} args={msg.args} />}
            {msg.kind === 'tool_result' && <ToolResultCard name={msg.name} content={msg.content} />}
          </div>
        ))
      )}
      {streaming && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
          <TypingIndicator />
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
