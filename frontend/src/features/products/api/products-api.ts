import type { components } from '../../../shared/api/generated/schema'
import { apiClient } from '../../../shared/api/client'

export type Product = components['schemas']['ProductRead']
export type ProductProfileUpdate = components['schemas']['ProductProfileUpdate']
export type ValidationResult = components['schemas']['ValidationResult']

export const productsApi = {
  listProducts: async (organizationId: string) =>
    (await apiClient.get<Product[]>(`/api/v1/organizations/${organizationId}/products`)).data,
  getProduct: async (productId: string) =>
    (await apiClient.get<Product>(`/api/v1/products/${productId}`)).data,
  updateProductProfile: async (productId: string, data: ProductProfileUpdate) =>
    (await apiClient.patch<Product>(`/api/v1/products/${productId}/profile`, data)).data,
  validateProduct: async (productId: string) =>
    (
      await apiClient.post<ValidationResult>(`/api/v1/products/${productId}/profile/validate`)
    ).data,
}
