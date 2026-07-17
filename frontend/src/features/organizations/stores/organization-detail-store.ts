import axios from 'axios'
import { create } from 'zustand'

import { organizationsApi, type Organization } from '../api/organizations-api'

interface OrganizationDetailState {
  organization: Organization | null
  loading: boolean
  submitting: boolean
  error: string | null
  saved: boolean
  load: (organizationId: string) => Promise<void>
  save: (organizationId: string, value: Record<string, unknown>) => Promise<void>
  incrementalSave: (organizationId: string, value: Record<string, unknown>) => Promise<void>
  reset: () => void
}

const messageFor = (error: unknown, fallback: string) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? fallback)
    : fallback

export const useOrganizationDetailStore = create<OrganizationDetailState>((set) => ({
  organization: null,
  loading: false,
  submitting: false,
  error: null,
  saved: false,
  reset: () => set({ organization: null, loading: false, submitting: false, error: null, saved: false }),
  load: async (organizationId) => {
    set({ loading: true, error: null, saved: false })
    try {
      const organization = await organizationsApi.getOrganization(organizationId)
      set({ organization, loading: false })
    } catch (error) {
      set({ error: messageFor(error, 'Unable to load organization.'), loading: false })
    }
  },
  save: async (organizationId, value) => {
    set({ submitting: true, error: null, saved: false })
    try {
      const { identity: identityValue, ...orgForm } = value
      const identity = identityValue as {
        name: string
        website: string
        primary_contact_email?: string
        thumbnail_url?: string
      }
      const organization = await organizationsApi.updateOrganizationProfile(organizationId, {
        form: orgForm,
        name: identity.name,
        website: identity.website,
        primary_contact_email: identity.primary_contact_email || null,
        thumbnail_url: identity.thumbnail_url || null,
      })
      const result = await organizationsApi.validateOrganization(organizationId)
      set({
        organization,
        submitting: false,
        saved: result.valid,
        error: result.valid ? null : `Missing: ${result.missing_sections.join(', ')}`,
      })
    } catch (error) {
      set({
        error: messageFor(error, 'Unable to save organization profile.'),
        submitting: false,
      })
    }
  },
  incrementalSave: async (organizationId, value) => {
    try {
      const { identity: identityValue, ...orgForm } = value
      const identity = identityValue as {
        name: string
        website: string
        primary_contact_email?: string
        thumbnail_url?: string
      }
      const organization = await organizationsApi.updateOrganizationProfile(organizationId, {
        form: orgForm,
        name: identity.name,
        website: identity.website,
        primary_contact_email: identity.primary_contact_email || null,
        thumbnail_url: identity.thumbnail_url || null,
      })
      set({ organization })
    } catch (error) {
      // Allow throwing to let component handle error
      throw error
    }
  },
}))
