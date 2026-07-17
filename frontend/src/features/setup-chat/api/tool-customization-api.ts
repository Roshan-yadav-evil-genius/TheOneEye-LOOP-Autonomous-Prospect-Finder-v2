import { apiClient } from '../../../shared/api/client'
import type { components } from '../../../shared/api/generated/schema'

export type ToolCustomizationRuleRead = components['schemas']['ToolCustomizationRuleRead']

export const getPublicToolCustomizations = async () => {
  return (await apiClient.get<ToolCustomizationRuleRead[]>('/api/v1/tool-customizations')).data
}
