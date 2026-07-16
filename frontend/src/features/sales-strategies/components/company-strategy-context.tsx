import { Card } from '../../../shared/components/card'
import { FormField } from '../../../shared/components/form-field'
import type { CompanySummary } from '../api/sales-strategy-api'

export function CompanyStrategyContext({ company }: { company: CompanySummary }) {
  return (
    <Card title="Strategy context">
      <div className="field-grid field-grid--cols">
        <FormField label="Selection reason" help="Why this company was added to the strategy.">
          <textarea
            className="control"
            readOnly
            rows={3}
            value={company.selection_reason || '—'}
          />
        </FormField>
        <FormField label="Funnel stage" help="Current stage in the strategy funnel for this company.">
          <input className="control" readOnly value={company.funnel_stage} />
        </FormField>
        <FormField
          label="Contact quota"
          help="Prospects registered versus the target for this company."
        >
          <input
            className="control"
            readOnly
            value={`${company.contacts_registered}/${company.contacts_target}`}
          />
        </FormField>
        <FormField
          label="Prospect queue"
          help="Whether prospect discovery can run for this company."
        >
          <input
            className="control"
            readOnly
            value={company.prospect_queue_status ?? 'Not eligible'}
          />
        </FormField>
        <FormField label="Blacklist status" help="Whether the company is excluded from active outreach.">
          <input
            className="control"
            readOnly
            value={company.is_blacklisted ? 'Blacklisted' : 'Active'}
          />
        </FormField>
        <FormField label="Blacklist reason" help="Why the company was blacklisted, if applicable.">
          <textarea
            className="control"
            readOnly
            rows={2}
            value={company.blacklist_reason ?? '—'}
          />
        </FormField>
      </div>
    </Card>
  )
}
