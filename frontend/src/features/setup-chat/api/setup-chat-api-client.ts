export interface ChatHistoryRead {
  thread_id: string
  messages: any[]
  can_resume: boolean
}

export interface StateSnapshot extends Record<string, any> {
  step_index?: number
  config?: Record<string, any>
  checkpoint?: Record<string, any>
  metadata?: Record<string, any>
  parent_config?: Record<string, any>
  pending_writes?: any[]
}

export type StateSnapshotRead = StateSnapshot


export interface ChatStreamRequest {
  message?: string
  mode?: 'ask' | 'act'
  retry?: boolean
  redo_last?: boolean
  thread_id?: string | null
  is_planner?: boolean
  config?: Record<string, any>
}

export type ChatStreamEvent = 
  | { kind: 'reasoning'; text: string; agent?: string; checkpoint_ns?: string }
  | { kind: 'content'; text: string; agent?: string; checkpoint_ns?: string }
  | { kind: 'metadata'; metadata: Record<string, any>; agent?: string; checkpoint_ns?: string }
  | { kind: 'tool_call'; id: string; name: string; args: unknown; agent?: string; checkpoint_ns?: string }
  | { kind: 'tool_result'; id: string; name: string; content: string; agent?: string; checkpoint_ns?: string }
  | { kind: 'done'; thread_id: string }
  | { kind: 'incomplete'; can_resume: boolean }
  | { kind: 'error'; message: string; can_resume?: boolean }

export const streamChatGeneric = async (
  url: string,
  data: ChatStreamRequest,
  onEvent: (event: ChatStreamEvent) => void
) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.statusText}`)
  }

  if (!response.body) {
    throw new Error('No response body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    
    // keep the last incomplete chunk in the buffer
    buffer = lines.pop() || ''

    for (const block of lines) {
      if (!block.trim()) continue
      
      let eventType = ''
      let eventData = ''

      const blockLines = block.split('\n')
      for (const line of blockLines) {
        if (line.startsWith('event:')) {
          eventType = line.slice('event:'.length).trim()
        } else if (line.startsWith('data:')) {
          eventData = line.slice('data:'.length).trim()
        }
      }

      if (eventData) {
        try {
          const parsed = JSON.parse(eventData)
          switch (eventType) {
            case 'reasoning':
              onEvent({ kind: 'reasoning', text: parsed.text, agent: parsed.agent, checkpoint_ns: parsed.checkpoint_ns })
              break
            case 'content':
              onEvent({ kind: 'content', text: parsed.text, agent: parsed.agent, checkpoint_ns: parsed.checkpoint_ns })
              break
            case 'metadata':
              onEvent({ kind: 'metadata', metadata: parsed, agent: parsed.agent, checkpoint_ns: parsed.checkpoint_ns })
              break
            case 'tool_call':
              onEvent({ kind: 'tool_call', id: parsed.id, name: parsed.name, args: parsed.args, agent: parsed.agent, checkpoint_ns: parsed.checkpoint_ns })
              break
            case 'tool_result':
              onEvent({ kind: 'tool_result', id: parsed.id, name: parsed.name, content: parsed.content, agent: parsed.agent, checkpoint_ns: parsed.checkpoint_ns })
              break
            case 'done':
              onEvent({ kind: 'done', thread_id: parsed.thread_id })
              break
            case 'incomplete':
              onEvent({ kind: 'incomplete', can_resume: parsed.can_resume })
              break
            case 'error':
              onEvent({ kind: 'error', message: parsed.message, can_resume: parsed.can_resume })
              break
          }
        } catch (e) {
          console.error('Failed to parse SSE data', e, eventData)
        }
      }
    }
  }
}
