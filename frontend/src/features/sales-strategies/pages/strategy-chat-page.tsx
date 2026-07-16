import { WorkspaceShell } from '../components/workspace-shell'
import { StrategyChatTab } from '../components/strategy-chat-tab'

export function StrategyChatPage() {
  return (
    <WorkspaceShell pageSubtitle="Chat with the AI agent to update the strategy profile.">
      <div style={{ marginTop: '24px' }}>
        <StrategyChatTab />
      </div>
    </WorkspaceShell>
  )
}
