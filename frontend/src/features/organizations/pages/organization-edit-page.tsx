import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { SplitFormChatLayout } from '../../../shared/components/split-form-chat-layout'
import { FormLiveEditor } from '../../forms/components/form-live-editor'
import { organizationTemplate } from '../../forms/form-definitions'
import { organizationFormSections } from '../../forms/form-field-schema'
import { organizationFormThemes } from '../../forms/form-themes'
import { SetupChatPanel } from '../../setup-chat/components/SetupChatPanel'
import { useOrganizationChatStore } from '../stores/organization-chat-store'
import { useOrganizationDetailStore } from '../stores/organization-detail-store'

function toFormValue(organization: {
  name: string
  website: string
  primary_contact_email: string | null
  org_form: Record<string, unknown>
}) {
  return {
    identity: {
      name: organization.name,
      website: organization.website,
      primary_contact_email: organization.primary_contact_email ?? '',
      thumbnail_url: (organization as any).thumbnail_url,
    },
    ...organizationTemplate,
    ...organization.org_form,
  }
}

export function OrganizationEditPage() {
  const { orgId = '' } = useParams()
  const { organization, loading, error, submitting, saved, load, save, reset } = useOrganizationDetailStore()
  const chatStore = useOrganizationChatStore()

  useEffect(() => {
    reset()
    void load(orgId)
    void chatStore.loadHistory(orgId)
    return () => reset()
  }, [orgId, load, reset])

  // Live synchronization: When AI Agent executes set_organization, reload form
  useEffect(() => {
    if (chatStore.profileDirtyFromChat) {
      chatStore.clearDirtyFlag()
      void load(orgId)
    }
  }, [chatStore.profileDirtyFromChat, chatStore, load, orgId])

  const handleSave = async (value: Record<string, unknown>) => {
    await save(orgId, value)
  }

  if (loading && !organization) {
    return <p className="muted">Loading organization profile…</p>
  }

  if (error && !organization) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return (
    <SplitFormChatLayout
      title={`Edit Organization: ${organization?.name ?? ''}`}
      subtitle="Interactive split-panel mode. Manually edit fields or work with the AI assistant."
      breadcrumbs={[
        { label: 'Organizations', to: '/orgs' },
        { label: organization?.name ?? 'Organization', to: `/orgs/${orgId}` },
        { label: 'Edit' },
      ]}
      leftPanel={
        organization ? (
          <FormLiveEditor
            title="Organization Form"
            sections={organizationFormSections}
            themes={organizationFormThemes}
            initialValue={toFormValue(organization)}
            submitting={submitting}
            serverError={error}
            saved={saved}
            onSubmit={handleSave}
          />
        ) : null
      }
      rightPanel={
        <SetupChatPanel
          title="Organization Assistant"
          threadId={`org-${orgId}`}
          entityId={orgId}
          agentDescription="Guides you in populating organization profile data."
          store={chatStore}
        />
      }
    />
  )
}
