import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import { Badge, DataTable } from '../../../shared/components/design-system'
import { Drawer } from '../../../shared/components/drawer'
import { ExpandablePanel } from '../../../shared/components/expandable-panel'
import { FormField } from '../../../shared/components/form-field'
import { KpiStrip } from '../../../shared/components/kpi-strip'
import { ReasonConfirmModal } from '../../../shared/components/modal'
import type { OutreachUpdate, ProspectRead } from '../api/sales-strategy-api'
import { CompanyProfileEditDrawer } from '../components/company-profile-edit-drawer'
import { CompanyProfileSection } from '../components/company-profile-section'
import { ContactRegistrationDrawer } from '../components/contact-registration-drawer'
import { WorkspaceShell } from '../components/workspace-shell'
import { useCompanyDetailStore } from '../stores/company-detail-store'

function draftFor(
  prospect: ProspectRead,
  drafts: Record<string, OutreachUpdate>,
): OutreachUpdate {
  return (
    drafts[prospect.prospect_profile_id] ?? {
      connection_request_status:
        prospect.connection_request_status as OutreachUpdate['connection_request_status'],
      received_response: prospect.received_response ?? undefined,
      response_sentiment: prospect.response_sentiment as OutreachUpdate['response_sentiment'],
      response_negative_reason: prospect.response_negative_reason ?? undefined,
    }
  )
}

export function CompanyDetailPage() {
  const { companyId = '', orgId = '', strategyId = '' } = useParams()
  const {
    blacklistCompany,
    blacklistProspect,
    detail,
    drafts,
    error,
    load,
    loading,
    registerContact,
    reset,
    saveOutreach,
    savingContact,
    savingProfile,
    setDraft,
    unblacklistCompany,
    unblacklistProspect,
    updateProfile,
  } = useCompanyDetailStore()

  const [selectedProspectId, setSelectedProspectId] = useState<string | null>(null)
  const [companyBlacklistOpen, setCompanyBlacklistOpen] = useState(false)
  const [profileEditOpen, setProfileEditOpen] = useState(false)
  const [contactRegisterOpen, setContactRegisterOpen] = useState(false)
  const [contactNotice, setContactNotice] = useState<string | null>(null)
  const [prospectBlacklistId, setProspectBlacklistId] = useState<string | null>(null)
  const [blacklistReason, setBlacklistReason] = useState('')
  const [blacklisting, setBlacklisting] = useState(false)

  useEffect(() => {
    reset()
    void load(strategyId, companyId)
    return () => reset()
  }, [companyId, load, reset, strategyId])

  if (loading && !detail) {
    return (
      <WorkspaceShell pageSubtitle="Loading company…">
        <p className="muted">Loading company…</p>
      </WorkspaceShell>
    )
  }

  if (!detail) {
    return (
      <WorkspaceShell pageSubtitle="Company not found">
        {error ? <p role="alert" className="error-banner">{error}</p> : null}
        <p className="muted">Company not found.</p>
      </WorkspaceShell>
    )
  }

  const profile =
    detail.profile && typeof detail.profile === 'object'
      ? (detail.profile as Record<string, unknown>)
      : null

  const selectedProspect =
    detail.prospects.find((p) => p.prospect_profile_id === selectedProspectId) ?? null
  const selectedDraft = selectedProspect ? draftFor(selectedProspect, drafts) : null

  const confirmCompanyBlacklist = async () => {
    if (!blacklistReason.trim()) return
    setBlacklisting(true)
    try {
      await blacklistCompany(strategyId, companyId, blacklistReason.trim())
      setCompanyBlacklistOpen(false)
      setBlacklistReason('')
    } finally {
      setBlacklisting(false)
    }
  }

  const confirmProspectBlacklist = async () => {
    if (!prospectBlacklistId || !blacklistReason.trim()) return
    setBlacklisting(true)
    try {
      await blacklistProspect(strategyId, companyId, prospectBlacklistId, blacklistReason.trim())
      setProspectBlacklistId(null)
      setBlacklistReason('')
    } finally {
      setBlacklisting(false)
    }
  }

  return (
    <WorkspaceShell
      pageTitle={detail.company.name}
      pageSubtitle={detail.company.domain}
      actions={
        <>
          <Button asChild variant="ghost">
            <Link to={`/orgs/${orgId}/sales-strategies/${strategyId}/companies`}>← Company</Link>
          </Button>
          {detail.company.is_blacklisted ? (
            <Button
              variant="ghost"
              onClick={() => void unblacklistCompany(strategyId, companyId)}
            >
              Unblacklist company
            </Button>
          ) : (
            <Button
              variant="danger"
              onClick={() => {
                setCompanyBlacklistOpen(true)
                setBlacklistReason('')
              }}
            >
              Blacklist company
            </Button>
          )}
        </>
      }
    >
      <KpiStrip
        items={[
          { label: 'Stage', value: detail.company.funnel_stage },
          {
            label: 'Contacts',
            value: `${detail.company.contacts_registered}/${detail.company.contacts_target}`,
          },
          {
            label: 'Queue',
            value: detail.company.prospect_queue_status ?? 'Not eligible',
          },
          {
            label: 'Status',
            value: detail.company.is_blacklisted ? 'Blacklisted' : 'Active',
          },
        ]}
      />

      {error ? <p role="alert" className="error-banner">{error}</p> : null}

      <ExpandablePanel title="Selection reason" summary={detail.company.selection_reason ? 'Set' : 'Empty'}>
        <p>{detail.company.selection_reason || '—'}</p>
        {detail.company.blacklist_reason ? (
          <p className="muted">Blacklist: {detail.company.blacklist_reason}</p>
        ) : null}
      </ExpandablePanel>

      <CompanyProfileSection profile={profile} onEdit={() => setProfileEditOpen(true)} />

      <div className="row-actions section-heading">
        <h2>Prospects</h2>
        <Button onClick={() => setContactRegisterOpen(true)}>Register contact</Button>
      </div>
      {contactNotice ? <p className="muted">{contactNotice}</p> : null}
      <DataTable
        headers={['Name', 'Role', 'Connection', 'Status', 'Actions']}
        empty={<p className="muted">No prospects registered for this company yet.</p>}
      >
        {detail.prospects.map((prospect) => {
          const draft = draftFor(prospect, drafts)
          return (
            <tr key={prospect.id}>
              <td>
                <strong>{prospect.full_name ?? 'Sparse profile'}</strong>
                {prospect.is_blacklisted ? <small>Blacklisted</small> : null}
              </td>
              <td>{prospect.job_title ?? 'Unknown'}</td>
              <td>{draft.connection_request_status ?? '—'}</td>
              <td>
                {prospect.is_blacklisted ? (
                  <Badge tone="danger">Blacklisted</Badge>
                ) : draft.response_sentiment ? (
                  <Badge tone={draft.response_sentiment === 'positive' ? 'success' : 'warning'}>
                    {draft.response_sentiment}
                  </Badge>
                ) : (
                  <Badge tone="info">Open</Badge>
                )}
              </td>
              <td className="row-actions">
                <Button
                  variant="ghost"
                  onClick={() => setSelectedProspectId(prospect.prospect_profile_id)}
                >
                  Outreach
                </Button>
                {prospect.is_blacklisted ? (
                  <Button
                    variant="ghost"
                    onClick={() =>
                      void unblacklistProspect(
                        strategyId,
                        companyId,
                        prospect.prospect_profile_id,
                      )
                    }
                  >
                    Unblacklist
                  </Button>
                ) : (
                  <Button
                    variant="danger"
                    onClick={() => {
                      setProspectBlacklistId(prospect.prospect_profile_id)
                      setBlacklistReason('')
                    }}
                  >
                    Blacklist
                  </Button>
                )}
              </td>
            </tr>
          )
        })}
      </DataTable>

      <CompanyProfileEditDrawer
        open={profileEditOpen}
        onOpenChange={setProfileEditOpen}
        profile={profile}
        saving={savingProfile}
        onSave={async (nextProfile) => {
          await updateProfile(strategyId, companyId, nextProfile)
          setProfileEditOpen(false)
        }}
      />

      <ContactRegistrationDrawer
        open={contactRegisterOpen}
        onOpenChange={setContactRegisterOpen}
        saving={savingContact}
        onSubmit={async (payload) => {
          const notice = await registerContact(strategyId, companyId, payload)
          if (notice === 'Registration failed.') return
          setContactNotice(notice)
          setContactRegisterOpen(false)
        }}
      />

      <Drawer
        open={selectedProspect != null && selectedDraft != null}
        onOpenChange={(open) => {
          if (!open) setSelectedProspectId(null)
        }}
        title={selectedProspect?.full_name ?? 'Prospect outreach'}
        description={selectedProspect?.job_title ?? undefined}
        footer={
          selectedProspect ? (
            <Button
              onClick={() =>
                void saveOutreach(strategyId, companyId, selectedProspect.prospect_profile_id)
              }
            >
              Save outreach
            </Button>
          ) : null
        }
      >
        {selectedProspect && selectedDraft ? (
          <div className="field-grid">
            <FormField label="LinkedIn" help="Open the prospect profile on LinkedIn.">
              <a href={selectedProspect.linkedin_url} target="_blank" rel="noreferrer">
                Open profile
              </a>
            </FormField>
            <FormField
              label="Selection reason"
              help="Why this prospect was chosen — set by the agent or operator."
            >
              <textarea
                className="control"
                readOnly
                rows={2}
                value={selectedProspect.selection_reason || '—'}
              />
            </FormField>
            <FormField
              label="Fit rationale"
              help="How this prospect matches the strategy ICP and buyer personas."
            >
              <textarea
                className="control"
                readOnly
                rows={2}
                value={selectedProspect.fit_rationale || '—'}
              />
            </FormField>
            <FormField
              label="Confidence"
              help="Agent confidence score for this prospect fit (0–100)."
            >
              <input
                className="control"
                readOnly
                value={
                  selectedProspect.confidence_score == null
                    ? '—'
                    : String(selectedProspect.confidence_score)
                }
              />
            </FormField>
            <FormField
              label="Connection"
              help="Status of your LinkedIn connection request to this prospect."
            >
              <select
                className="control"
                value={selectedDraft.connection_request_status ?? ''}
                onChange={(event) =>
                  setDraft(selectedProspect.prospect_profile_id, {
                    ...selectedDraft,
                    connection_request_status: event.target
                      .value as OutreachUpdate['connection_request_status'],
                  })
                }
              >
                <option value="">Not recorded</option>
                <option value="sent">sent</option>
                <option value="ignored">ignored</option>
                <option value="accepted">accepted</option>
              </select>
            </FormField>
            <FormField label="Response" help="Whether the prospect replied to outreach.">
              <select
                className="control"
                value={
                  selectedDraft.received_response == null
                    ? ''
                    : selectedDraft.received_response
                      ? 'yes'
                      : 'no'
                }
                onChange={(event) =>
                  setDraft(selectedProspect.prospect_profile_id, {
                    ...selectedDraft,
                    received_response:
                      event.target.value === ''
                        ? undefined
                        : event.target.value === 'yes',
                  })
                }
              >
                <option value="">Unknown</option>
                <option value="yes">yes</option>
                <option value="no">no</option>
              </select>
            </FormField>
            <FormField label="Sentiment" help="Tone of the prospect reply, if they responded.">
              <select
                className="control"
                value={selectedDraft.response_sentiment ?? ''}
                onChange={(event) =>
                  setDraft(selectedProspect.prospect_profile_id, {
                    ...selectedDraft,
                    response_sentiment: event.target
                      .value as OutreachUpdate['response_sentiment'],
                  })
                }
              >
                <option value="">n/a</option>
                <option value="positive">positive</option>
                <option value="negative">negative</option>
              </select>
            </FormField>
            <FormField
              label="Negative reason"
              help="Brief note when the reply sentiment is negative."
            >
              <input
                className="control"
                value={selectedDraft.response_negative_reason ?? ''}
                onChange={(event) =>
                  setDraft(selectedProspect.prospect_profile_id, {
                    ...selectedDraft,
                    response_negative_reason: event.target.value,
                  })
                }
              />
            </FormField>
          </div>
        ) : null}
      </Drawer>

      <ReasonConfirmModal
        open={companyBlacklistOpen}
        onOpenChange={setCompanyBlacklistOpen}
        title="Blacklist company"
        description="Why blacklist this company for the strategy?"
        confirmLabel="Blacklist"
        reason={blacklistReason}
        onReasonChange={setBlacklistReason}
        onConfirm={() => void confirmCompanyBlacklist()}
        confirming={blacklisting}
      />

      <ReasonConfirmModal
        open={prospectBlacklistId != null}
        onOpenChange={(open) => {
          if (!open) setProspectBlacklistId(null)
        }}
        title="Blacklist prospect"
        description="Why blacklist this prospect?"
        confirmLabel="Blacklist"
        reason={blacklistReason}
        onReasonChange={setBlacklistReason}
        onConfirm={() => void confirmProspectBlacklist()}
        confirming={blacklisting}
      />
    </WorkspaceShell>
  )
}
