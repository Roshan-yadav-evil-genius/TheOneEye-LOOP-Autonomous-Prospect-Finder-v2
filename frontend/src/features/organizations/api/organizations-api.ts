import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type Organization = components['schemas']['OrganizationRead']
export type OrganizationProfileUpdate = components['schemas']['OrganizationProfileUpdate']
export type ValidationResult = components['schemas']['ValidationResult']

export const organizationsApi = {
  listOrganizations: async () =>
    (await apiClient.get<Organization[]>('/api/v1/organizations')).data,
  getOrganization: async (organizationId: string) =>
    (await apiClient.get<Organization>(`/api/v1/organizations/${organizationId}`)).data,
  updateOrganizationProfile: async (organizationId: string, data: OrganizationProfileUpdate) =>
    (
      await apiClient.patch<Organization>(
        `/api/v1/organizations/${organizationId}/profile`,
        data,
      )
    ).data,
  validateOrganization: async (organizationId: string) =>
    (
      await apiClient.post<ValidationResult>(
        `/api/v1/organizations/${organizationId}/profile/validate`,
      )
    ).data,
}
