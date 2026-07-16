import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

type OrganizationCreate = components['schemas']['OrganizationCreate']
type OrganizationRead = components['schemas']['OrganizationRead']
type ProductCreate = components['schemas']['ProductCreate']
type ProductRead = components['schemas']['ProductRead']
type SalesStrategyCreate = components['schemas']['SalesStrategyCreate']
type SalesStrategyRead = components['schemas']['SalesStrategyRead']
export type ValidationResult = components['schemas']['ValidationResult']
export type FormMarkdownTemplate = components['schemas']['FormMarkdownTemplate']

export type FormTemplateKey = 'organization' | 'product' | 'sales-strategy'

const templatePath: Record<FormTemplateKey, string> = {
  organization: '/api/v1/forms/organization/template',
  product: '/api/v1/forms/product/template',
  'sales-strategy': '/api/v1/forms/sales-strategy/template',
}

export const formsApi = {
  downloadTemplate: async (formKey: FormTemplateKey) =>
    (await apiClient.get<FormMarkdownTemplate>(templatePath[formKey])).data,
  createOrganization: async (data: OrganizationCreate) =>
    (await apiClient.post<OrganizationRead>('/api/v1/organizations', data)).data,
  validateOrganization: async (organizationId: string) =>
    (
      await apiClient.post<ValidationResult>(
        `/api/v1/organizations/${organizationId}/profile/validate`,
      )
    ).data,
  createProduct: async (organizationId: string, data: ProductCreate) =>
    (
      await apiClient.post<ProductRead>(
        `/api/v1/organizations/${organizationId}/products`,
        data,
      )
    ).data,
  validateProduct: async (productId: string) =>
    (
      await apiClient.post<ValidationResult>(
        `/api/v1/products/${productId}/profile/validate`,
      )
    ).data,
  createStrategy: async (productId: string, data: SalesStrategyCreate) =>
    (
      await apiClient.post<SalesStrategyRead>(
        `/api/v1/products/${productId}/sales-strategies`,
        data,
      )
    ).data,
}
