import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import { DataTable, SearchField } from '../../../shared/components/design-system'
import { Drawer } from '../../../shared/components/drawer'
import { FormField } from '../../../shared/components/form-field'
import { KpiStrip } from '../../../shared/components/kpi-strip'
import { ReasonConfirmModal } from '../../../shared/components/modal'
import { WorkspaceShell } from '../components/workspace-shell'
import { useRecordsStore } from '../stores/records-store'

export function RecordsPage() {
  const { orgId, strategyId = '' } = useParams()
  const { blacklist, companies, error, load, progress, register, unblacklist, validate } =
    useRecordsStore()
  const [query, setQuery] = useState('')
  const [registerOpen, setRegisterOpen] = useState(false)
  const [name, setName] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [selectionReason, setSelectionReason] = useState('')
  const [registering, setRegistering] = useState(false)
  const [blacklistTarget, setBlacklistTarget] = useState<string | null>(null)
  const [blacklistReason, setBlacklistReason] = useState('')
  const [blacklisting, setBlacklisting] = useState(false)

  const filtered = useMemo(
    () =>
      companies.filter((company) =>
        `${company.name} ${company.domain}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [companies, query],
  )

  useEffect(() => {
    void load(strategyId)
  }, [load, strategyId])

  const submitManualRegister = async () => {
    setRegistering(true)
    try {
      await register(strategyId, {
        name: name.trim(),
        website_url: websiteUrl.trim(),
        selection_reason: selectionReason.trim(),
      })
      setName('')
      setWebsiteUrl('')
      setSelectionReason('')
      setRegisterOpen(false)
    } catch {
      // Store surfaces the error; keep operator input for recovery.
    } finally {
      setRegistering(false)
    }
  }

  const confirmBlacklist = async () => {
    if (!blacklistTarget || !blacklistReason.trim()) return
    setBlacklisting(true)
    try {
      await blacklist(strategyId, blacklistTarget, blacklistReason.trim())
      setBlacklistTarget(null)
      setBlacklistReason('')
    } finally {
      setBlacklisting(false)
    }
  }

  return (
    <WorkspaceShell
      pageSubtitle="Companies table for this strategy. Register manually when offline research is ready."
      actions={
        <Button type="button" onClick={() => setRegisterOpen(true)}>
          Register company
        </Button>
      }
    >
      <KpiStrip
        items={[
          {
            label: 'Companies',
            value: `${progress?.companies_registered ?? 0}/${progress?.target_companies ?? 0}`,
          },
          { label: 'Validated', value: String(progress?.companies_validated ?? 0) },
          {
            label: 'Contacts',
            value: `${progress?.contacts_registered ?? 0}/${progress?.contacts_target ?? 0}`,
          },
        ]}
      />
      {error ? <p role="alert" className="error-banner">{error}</p> : null}
      <SearchField
        value={query}
        onChange={setQuery}
        placeholder="Search companies"
        label="Search companies"
      />
      <DataTable
        headers={['Company', 'Stage', 'Queue', 'Contacts', 'Actions']}
        empty={<p className="muted">No companies match this filter.</p>}
      >
        {filtered.map((company) => (
          <tr key={company.id}>
            <td>
              <Link
                to={`/orgs/${orgId}/sales-strategies/${strategyId}/companies/${company.company_id}`}
              >
                <strong>{company.name}</strong>
                <small>{company.domain}</small>
              </Link>
            </td>
            <td>
              <span className="badge">{company.funnel_stage}</span>
            </td>
            <td>{company.prospect_queue_status ?? 'Not eligible'}</td>
            <td>
              {company.contacts_registered}/{company.contacts_target}
            </td>
            <td className="row-actions">
              {company.funnel_stage === 'registered' && !company.is_blacklisted ? (
                <Button onClick={() => void validate(strategyId, company.company_id)}>
                  Mark valid
                </Button>
              ) : null}
              {company.is_blacklisted ? (
                <Button
                  variant="ghost"
                  onClick={() => void unblacklist(strategyId, company.company_id)}
                >
                  Unblacklist
                </Button>
              ) : (
                <Button
                  variant="danger"
                  onClick={() => {
                    setBlacklistTarget(company.company_id)
                    setBlacklistReason('')
                  }}
                >
                  Blacklist
                </Button>
              )}
            </td>
          </tr>
        ))}
      </DataTable>

      <Drawer
        open={registerOpen}
        onOpenChange={setRegisterOpen}
        title="Register company"
        description="Operators may register a company when validating agent research offline. Selection reason is required for audit."
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setRegisterOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={
                registering || !name.trim() || !websiteUrl.trim() || !selectionReason.trim()
              }
              onClick={() => void submitManualRegister()}
            >
              {registering ? 'Registering…' : 'Register company'}
            </Button>
          </>
        }
      >
        <div className="field-grid">
          <FormField label="Company name" required help="Legal or brand name as it appears publicly.">
            <input
              className="control"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </FormField>
          <FormField label="Website URL" required help="Canonical company website, including https://.">
            <input
              className="control"
              type="url"
              value={websiteUrl}
              onChange={(event) => setWebsiteUrl(event.target.value)}
              required
            />
          </FormField>
          <FormField
            label="Selection reason"
            required
            help="Why this company fits the strategy — stored for audit and agent context."
          >
            <textarea
              className="control"
              value={selectionReason}
              onChange={(event) => setSelectionReason(event.target.value)}
              rows={3}
              required
            />
          </FormField>
        </div>
      </Drawer>

      <ReasonConfirmModal
        open={blacklistTarget != null}
        onOpenChange={(open) => {
          if (!open) {
            setBlacklistTarget(null)
            setBlacklistReason('')
          }
        }}
        title="Blacklist company"
        description="This removes the company from active outreach for this strategy."
        confirmLabel="Blacklist"
        reason={blacklistReason}
        onReasonChange={setBlacklistReason}
        onConfirm={() => void confirmBlacklist()}
        confirming={blacklisting}
      />
    </WorkspaceShell>
  )
}
