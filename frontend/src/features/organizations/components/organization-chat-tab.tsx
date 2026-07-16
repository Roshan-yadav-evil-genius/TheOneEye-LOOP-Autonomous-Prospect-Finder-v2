import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useOrganizationChatStore } from '../stores/organization-chat-store'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'

export function OrganizationChatTab() {
  const { orgId = '' } = useParams()
  const store = useOrganizationChatStore()

  const { loadHistory, reset } = store

  useEffect(() => {
    void loadHistory(orgId)
    return () => reset()
  }, [orgId, loadHistory, reset])

  return (
    <SetupChatPanel 
      title="Organization Setup Assistant"
      threadId={`org_${orgId}_setup_chat`}
      entityId={orgId}
      agentDescription="can update organization profile; switch to Details tab to see saved fields"
      store={store}
    />
  )
}
