import { useState } from 'react'
import { Button } from '../../../shared/components/button'

export function ChatComposer({ 
  onSend, 
  onContinue, 
  disabled, 
  incompleteTurn = false,
  canResume = false,
  noInputRequired = false
}: { 
  onSend: (msg: string) => void, 
  onContinue: () => void, 
  disabled: boolean, 
  incompleteTurn?: boolean,
  canResume?: boolean,
  noInputRequired?: boolean
}) {
  const [text, setText] = useState('')

  const handleSend = () => {
    if (disabled) return
    if (!noInputRequired && !text.trim()) return
    onSend(noInputRequired ? '' : text.trim())
    setText('')
  }

  const handleContinue = () => {
    if (disabled) return
    onContinue()
  }

  const buttonText = incompleteTurn 
    ? (canResume ? 'Continue' : 'Retry') 
    : (noInputRequired ? 'Start' : 'Send')

  const showWaitPlaceholder = incompleteTurn
  const disableInput = disabled || incompleteTurn || noInputRequired

  const placeholderText = showWaitPlaceholder
    ? 'Waiting for AI to finish turn...'
    : (noInputRequired ? 'No input required. Click Start to run the Planner agent.' : 'Type a message...')

  return (
    <div style={{ display: 'flex', gap: '8px', marginTop: '16px', alignItems: 'flex-end' }}>
      <textarea
        value={showWaitPlaceholder || noInputRequired ? '' : text}
        onChange={(e) => setText(e.target.value)}
        disabled={disableInput}
        placeholder={placeholderText}
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
          opacity: disableInput ? 0.6 : 1,
          cursor: disableInput ? 'not-allowed' : 'text'
        }}
        rows={1}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            if (incompleteTurn) {
              handleContinue()
            } else {
              handleSend()
            }
          }
        }}
      />
      <Button
        type="button"
        onClick={incompleteTurn ? handleContinue : handleSend}
        disabled={disabled || (!incompleteTurn && !noInputRequired && !text.trim())}
      >
        {buttonText}
      </Button>
    </div>
  )
}
