import { useState } from 'react'
import { Button } from '../../../../shared/components/button'

export function ChatComposer({ onSend, disabled }: { onSend: (msg: string) => void, disabled: boolean }) {
  const [text, setText] = useState('')

  const handleSend = () => {
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <div style={{ display: 'flex', gap: '8px', marginTop: '16px', alignItems: 'flex-end' }}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder="Type a message..."
        style={{
          flex: 1,
          padding: '10px 12px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border-default)',
          background: 'var(--color-bg-elevated)',
          color: 'var(--color-text-primary)',
          resize: 'none',
          minHeight: '44px',
          maxHeight: '120px',
          fontFamily: 'inherit',
          opacity: disabled ? 0.6 : 1,
          cursor: disabled ? 'not-allowed' : 'text'
        }}
        rows={1}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
          }
        }}
      />
      <Button type="button" onClick={handleSend} disabled={disabled || !text.trim()}>
        Send
      </Button>
    </div>
  )
}
