import axios from 'axios'
import { create } from 'zustand'

import { formsApi } from '../api/forms-api'

interface SetupState {
  organizationId: string | null
  productId: string | null
  strategyId: string | null
  error: string | null
  submitting: boolean
  createOrganization: (value: Record<string, unknown>) => Promise<void>
  createProduct: (organizationId: string, value: Record<string, unknown>) => Promise<void>
  createStrategy: (productId: string, value: Record<string, unknown>) => Promise<void>
  clearStrategyCreation: () => void
}

const errorMessage = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'The form could not be submitted.')
    : 'The form could not be submitted.'

export const useSetupStore = create<SetupState>((set) => ({
  organizationId: null,
  productId: null,
  strategyId: null,
  error: null,
  submitting: false,
  clearStrategyCreation: () => set({ strategyId: null, error: null, submitting: false }),
  createOrganization: async (value) => {
    set({ error: null, submitting: true })
    try {
      const { identity: identityValue, ...orgForm } = value
      const identity = identityValue as Record<string, string>
      const organization = await formsApi.createOrganization({
        name: identity.name,
        website: identity.website,
        primary_contact_email: identity.primary_contact_email || null,
        thumbnail_url: identity.thumbnail_url || null,
        org_form: orgForm,
      })
      const result = await formsApi.validateOrganization(organization.id)
      set({
        organizationId: organization.id,
        error: result.valid ? null : `Missing: ${result.missing_sections.join(', ')}`,
        submitting: false,
      })
    } catch (error) {
      set({ error: errorMessage(error), submitting: false })
    }
  },
  createProduct: async (organizationId, value) => {
    set({ error: null, submitting: true })
    try {
      const { identity: identityValue, ...icpForm } = value
      const identity = identityValue as { name: string; kind: 'product' | 'service'; thumbnail_url?: string }
      const product = await formsApi.createProduct(organizationId, {
        name: identity.name,
        kind: identity.kind,
        thumbnail_url: identity.thumbnail_url || null,
        icp_form: { form_version: '2.0', ...icpForm },
      })
      const result = await formsApi.validateProduct(product.id)
      set({
        productId: product.id,
        error: result.valid ? null : `Missing: ${result.missing_sections.join(', ')}`,
        submitting: false,
      })
    } catch (error) {
      set({ error: errorMessage(error), submitting: false })
    }
  },
  createStrategy: async (productId, value) => {
    set({ error: null, submitting: true })
    try {
      const overview = (value.overview || {}) as { thumbnail_url?: string }
      const strategy = await formsApi.createStrategy(productId, {
        thumbnail_url: overview.thumbnail_url || null,
        sales_strategy_form: { form_version: '2.0', ...value },
      })
      set({ strategyId: strategy.id, submitting: false })
    } catch (error) {
      set({ error: errorMessage(error), submitting: false })
    }
  },
}))
