import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatUiMessage } from '../stores/store-factory'
import { ReasoningCard } from './reasoning-card'
import { ToolCallCard } from './tool-call-card'
import { ToolResultCard } from './tool-result-card'
import { TypingIndicator } from './typing-indicator'
import { getPublicToolCustomizations } from '../api/tool-customization-api'
import type { ToolCustomizationRuleRead } from '../api/tool-customization-api'
import { useState } from 'react'
import { sharedMarkdownComponents, userMarkdownComponents } from './shared-markdown-components'

export function ChatMessageList({ messages, streaming, emptyMessage }: { messages: ChatUiMessage[], streaming?: boolean, emptyMessage?: string }) {
  const endRef = useRef<HTMLDivElement>(null)
  const [rules, setRules] = useState<ToolCustomizationRuleRead[]>([])

  useEffect(() => {
    void getPublicToolCustomizations().then(setRules).catch(console.error)
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="chat-message-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflowY: 'auto', padding: '16px 4px' }}>
      {messages.length === 0 ? (
        <p className="muted" style={{ textAlign: 'center', margin: 'auto' }}>{emptyMessage || 'No messages yet. Say hello!'}</p>
      ) : (
        messages.map((msg) => (
          <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.kind === 'user' ? 'flex-end' : 'flex-start', width: '100%' }}>
            {msg.kind === 'user' ? (
              <div style={{ background: 'var(--color-accent-primary)', color: 'var(--color-accent-foreground)', padding: '8px 12px', borderRadius: '16px 16px 0 16px', maxWidth: '85%', wordBreak: 'break-word' }}>
                <ReactMarkdown components={userMarkdownComponents as any}>
                  {msg.content}
                </ReactMarkdown>
              </div>
            ) : (
              <div style={{ width: '100%', maxWidth: '85%' }}>
                {msg.kind === 'assistant' && (
                  <div className="markdown-chat" style={{ background: 'var(--color-bg-elevated)', color: 'var(--color-text-primary)', padding: '8px 16px', borderRadius: '16px 16px 16px 0', width: '100%', wordBreak: 'break-word', border: '1px solid var(--color-border-default)' }}>
                    <ReactMarkdown components={sharedMarkdownComponents as any}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
                {msg.kind === 'reasoning' && <ReasoningCard text={msg.text} />}
                {msg.kind === 'tool_call' && <ToolCallCard name={msg.name} args={msg.args} rules={rules} />}
                {msg.kind === 'tool_result' && <ToolResultCard name={msg.name} content={msg.content} rules={rules} />}
              </div>
            )}
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
