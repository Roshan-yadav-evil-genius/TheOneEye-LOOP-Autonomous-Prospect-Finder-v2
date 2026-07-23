import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type SalesStrategy = components['schemas']['SalesStrategyRead']
export type SalesStrategyBundle = components['schemas']['SalesStrategyBundle']
export type CompanySummary = components['schemas']['CompanySummary']
export type CompanyDetail = components['schemas']['CompanyDetail']
export type ProspectRead = components['schemas']['ProspectRead']
export type Progress = components['schemas']['ProgressRead']
export type ProcessStatus = components['schemas']['ProcessStatus']
export type Whiteboard = components['schemas']['WhiteboardRead']
export type AgentRun = components['schemas']['AgentRunSummary']
export type ThreadSnapshot = components['schemas']['ThreadSnapshot']
export type OutreachUpdate = components['schemas']['OutreachUpdate']
export type RegisterCompanyRequest = components['schemas']['RegisterCompanyRequest']
export type RegisterCompanyResult = components['schemas']['RegisterCompanyResult']
export type RegisterContactRequest = components['schemas']['RegisterContactRequest']
export type RegistrationResult = components['schemas']['RegistrationResult']
export type CompanyProfileUpdate = components['schemas']['CompanyProfileUpdate']
export type SalesStrategyProfileUpdate = components['schemas']['SalesStrategyProfileUpdate']

const strategyPath = (strategyId: string) => `/api/v1/sales-strategies/${strategyId}`

export const salesStrategyApi = {
  listStrategies: async (productId: string) =>
    (
      await apiClient.get<SalesStrategy[]>(`/api/v1/products/${productId}/sales-strategies`)
    ).data,
  createStrategy: async (productId: string, payload: Record<string, unknown> = {}) =>
    (
      await apiClient.post<SalesStrategy>(`/api/v1/products/${productId}/sales-strategies`, payload)
    ).data,
  getStrategy: async (strategyId: string) =>
    (await apiClient.get<SalesStrategy>(`${strategyPath(strategyId)}/strategy`)).data,
  updateStrategyProfile: async (strategyId: string, data: SalesStrategyProfileUpdate) =>
    (await apiClient.patch<SalesStrategy>(`${strategyPath(strategyId)}/strategy`, data)).data,
  deleteStrategy: async (strategyId: string) => {
    await apiClient.delete(`/api/v1/sales-strategies/${strategyId}`)
  },
  getBundle: async (strategyId: string) =>
    (await apiClient.get<SalesStrategyBundle>(`${strategyPath(strategyId)}/bundle`)).data,
  getRecords: async (strategyId: string) =>
    (await apiClient.get<CompanySummary[]>(`${strategyPath(strategyId)}/companies`)).data,
  getProgress: async (strategyId: string) =>
    (await apiClient.get<Progress>(`${strategyPath(strategyId)}/progress`)).data,
  getCompany: async (strategyId: string, companyId: string) =>
    (
      await apiClient.get<CompanyDetail>(
        `${strategyPath(strategyId)}/companies/${companyId}`,
      )
    ).data,
  updateCompanyProfile: async (
    strategyId: string,
    companyId: string,
    payload: CompanyProfileUpdate,
  ) =>
    (
      await apiClient.patch<CompanyDetail>(
        `${strategyPath(strategyId)}/companies/${companyId}/profile`,
        payload,
      )
    ).data,
  registerContact: async (
    strategyId: string,
    companyId: string,
    payload: RegisterContactRequest,
  ) =>
    (
      await apiClient.post<RegistrationResult>(
        `${strategyPath(strategyId)}/companies/${companyId}/prospects`,
        payload,
      )
    ).data,
  registerCompany: async (strategyId: string, payload: RegisterCompanyRequest) =>
    (
      await apiClient.post<RegisterCompanyResult>(
        `${strategyPath(strategyId)}/companies`,
        payload,
      )
    ).data,
  validateCompany: async (strategyId: string, companyId: string) =>
    (
      await apiClient.post<CompanySummary>(
        `${strategyPath(strategyId)}/companies/${companyId}/validate`,
      )
    ).data,
  blacklistCompany: async (strategyId: string, companyId: string, reason: string) =>
    (
      await apiClient.post<CompanySummary>(
        `${strategyPath(strategyId)}/companies/${companyId}/blacklist`,
        { blacklist_reason: reason },
      )
    ).data,
  unblacklistCompany: async (strategyId: string, companyId: string) =>
    (
      await apiClient.post<CompanySummary>(
        `${strategyPath(strategyId)}/companies/${companyId}/unblacklist`,
      )
    ).data,
  blacklistProspect: async (
    strategyId: string,
    companyId: string,
    prospectId: string,
    reason: string,
  ) => {
    await apiClient.post(
      `${strategyPath(strategyId)}/companies/${companyId}/prospects/${prospectId}/blacklist`,
      { blacklist_reason: reason },
    )
  },
  unblacklistProspect: async (
    strategyId: string,
    companyId: string,
    prospectId: string,
  ) => {
    await apiClient.post(
      `${strategyPath(strategyId)}/companies/${companyId}/prospects/${prospectId}/unblacklist`,
    )
  },
  updateOutreach: async (
    strategyId: string,
    companyId: string,
    prospectId: string,
    update: OutreachUpdate,
  ) => {
    await apiClient.patch(
      `${strategyPath(strategyId)}/companies/${companyId}/prospects/${prospectId}/outreach`,
      update,
    )
  },
  processStatus: async (strategyId: string, role: string) =>
    (
      await apiClient.get<ProcessStatus>(
        `${strategyPath(strategyId)}/agents/${role}/status`,
      )
    ).data,
  startProcess: async (strategyId: string, role: string) =>
    (
      await apiClient.post<ProcessStatus>(
        `${strategyPath(strategyId)}/agents/${role}/start`,
      )
    ).data,
  stopProcess: async (strategyId: string, role: string) =>
    (
      await apiClient.post<ProcessStatus>(
        `${strategyPath(strategyId)}/agents/${role}/stop`,
      )
    ).data,
  getWhiteboard: async (strategyId: string, role: string) =>
    (
      await apiClient.get<Whiteboard>(
        `${strategyPath(strategyId)}/agents/${role}/whiteboard`,
      )
    ).data,
  updateWhiteboard: async (strategyId: string, role: string, content: string) =>
    (
      await apiClient.patch<Whiteboard>(
        `${strategyPath(strategyId)}/agents/${role}/whiteboard`,
        { content },
      )
    ).data,
  getThreads: async (strategyId: string) =>
    (await apiClient.get<AgentRun[]>(`${strategyPath(strategyId)}/threads`)).data,
  getSnapshot: async (strategyId: string, threadId: string) =>
    (
      await apiClient.get<ThreadSnapshot>(
        `${strategyPath(strategyId)}/snapshots/${encodeURIComponent(threadId)}`,
      )
    ).data,
  processEventsUrl: (strategyId: string, role: string) =>
    `${apiClient.defaults.baseURL ?? ''}${strategyPath(strategyId)}/agents/${role}/events`,
}
