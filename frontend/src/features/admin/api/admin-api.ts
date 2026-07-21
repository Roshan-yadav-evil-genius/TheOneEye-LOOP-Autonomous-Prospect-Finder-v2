import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type AuditEvent = components['schemas']['AuditEventRead']
export type DeadLetter = components['schemas']['DeadLetterRead']
export type JobRun = components['schemas']['JobRunRead']
export type Schedule = components['schemas']['ScheduledTaskRead']
export type ToolCustomizationRuleCreate = components['schemas']['ToolCustomizationRuleCreate']
export type ToolCustomizationRuleRead = components['schemas']['ToolCustomizationRuleRead']

export const adminApi = {
  audit: async () => (await apiClient.get<AuditEvent[]>('/api/v1/admin/audit')).data,
  deadLetters: async () =>
    (await apiClient.get<DeadLetter[]>('/api/v1/admin/dead-letters')).data,
  jobs: async () => (await apiClient.get<JobRun[]>('/api/v1/admin/jobs')).data,
  schedules: async () =>
    (await apiClient.get<Schedule[]>('/api/v1/admin/schedules')).data,
  replay: async (id: string) =>
    (await apiClient.post(`/api/v1/admin/dead-letters/${id}/replay`)).data,
  discard: async (id: string) =>
    apiClient.post(`/api/v1/admin/dead-letters/${id}/discard`),
  
  // Tool Customizations
  toolCustomizations: async () =>
    (await apiClient.get<ToolCustomizationRuleRead[]>('/api/v1/admin/tool-customizations')).data,
  createToolCustomization: async (data: ToolCustomizationRuleCreate) =>
    (await apiClient.post<ToolCustomizationRuleRead>('/api/v1/admin/tool-customizations', data)).data,
  updateToolCustomization: async (id: string, data: ToolCustomizationRuleCreate) =>
    (await apiClient.put<ToolCustomizationRuleRead>(`/api/v1/admin/tool-customizations/${id}`, data)).data,
  deleteToolCustomization: async (id: string) =>
    apiClient.delete(`/api/v1/admin/tool-customizations/${id}`),
  uploadIcon: async (ruleId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return (await apiClient.post<{url: string}>(`/api/v1/admin/tool-customizations/${ruleId}/icon`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })).data
  }
}
