import { apiClient } from '../../../shared/api/client'

export interface AgentRunSummary {
  id: string
  agent_role: string
  effort_prefix: string
  primary_thread_id: string
  company_id?: string | null
  sales_strategy_prospect_id?: string | null
  status: string
  attempt_iteration: number
  contact_attempt_iteration?: number | null
  child_thread_ids: string[]
  created_at: string
}

export interface EffortDetailRead {
  id: string
  sales_strategy_id: string
  product_id: string
  company_id?: string | null
  sales_strategy_prospect_id?: string | null
  agent_role: string
  effort_prefix: string
  primary_thread_id: string
  status: string
  attempt_iteration: number
  contact_attempt_iteration?: number | null
  child_thread_ids: string[]
  active_subagent_threads?: Record<string, any>
  created_at: string
  completed_at?: string | null
}

export async function getCompanyFinderEfforts(strategyId: string): Promise<AgentRunSummary[]> {
  const res = await apiClient.get<AgentRunSummary[]>(
    `/api/v1/loop/strategies/${strategyId}/efforts?role=company-finder`
  )
  return res.data
}

export async function getContactFinderEfforts(
  strategyId: string,
  companyId?: string
): Promise<AgentRunSummary[]> {
  if (companyId) {
    const res = await apiClient.get<AgentRunSummary[]>(
      `/api/v1/loop/strategies/${strategyId}/companies/${companyId}/efforts`
    )
    return res.data
  }
  const res = await apiClient.get<AgentRunSummary[]>(
    `/api/v1/loop/strategies/${strategyId}/efforts?role=contact-finder`
  )
  return res.data
}

export async function getEffortDetail(effortPrefix: string): Promise<EffortDetailRead> {
  const res = await apiClient.get<EffortDetailRead>(
    `/api/v1/loop/efforts/${encodeURIComponent(effortPrefix)}`
  )
  return res.data
}
