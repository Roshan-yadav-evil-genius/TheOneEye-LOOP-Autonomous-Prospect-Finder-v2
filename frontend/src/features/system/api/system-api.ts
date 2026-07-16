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
