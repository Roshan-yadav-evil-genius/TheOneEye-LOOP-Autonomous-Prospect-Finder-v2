import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useStrategyChatStore } from '../stores/strategy-chat-store'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'

export function StrategyChatTab() {
  const { strategyId = '' } = useParams()
  const store = useStrategyChatStore()

  const { loadHistory, reset } = store

  useEffect(() => {
    void loadHistory(strategyId)
    return () => reset()
  }, [strategyId, loadHistory, reset])

  return (
    <SetupChatPanel 
      title="Sales Strategy Setup Assistant"
      threadId={`strategy_${strategyId}_setup_chat`}
      entityId={strategyId}
      agentDescription="can update strategy profile; switch to Details tab to see saved fields"
      store={store}
    />
  )
}
