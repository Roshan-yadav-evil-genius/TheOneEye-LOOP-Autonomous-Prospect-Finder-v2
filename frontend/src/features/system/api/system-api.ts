import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type BuildInfo = components['schemas']['BuildInfo']
export type HealthStatus = components['schemas']['HealthStatus']

export async function getLiveness(): Promise<HealthStatus> {
  const response = await apiClient.get<HealthStatus>('/health/live')
  return response.data
}

export async function getBuildInfo(): Promise<BuildInfo> {
  const response = await apiClient.get<BuildInfo>('/version')
  return response.data
}

export async function getGlobalThreads(): Promise<string[]> {
  const response = await apiClient.get<string[]>('/api/v1/threads')
  return response.data
}

export async function deleteGlobalThread(threadId: string): Promise<void> {
  await apiClient.delete(`/api/v1/threads/${encodeURIComponent(threadId)}`)
}
