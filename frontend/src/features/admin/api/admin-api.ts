import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type AuditEvent = components['schemas']['AuditEventRead']
export type DeadLetter = components['schemas']['DeadLetterRead']
export type JobRun = components['schemas']['JobRunRead']
export type Schedule = components['schemas']['ScheduledTaskRead']

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
}
