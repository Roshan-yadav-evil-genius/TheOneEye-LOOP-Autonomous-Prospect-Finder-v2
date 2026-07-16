import axios from 'axios'
import { create } from 'zustand'

import { organizationsApi, type Organization } from '../api/organizations-api'

interface OrganizationsState {
  organizations: Organization[]
  loading: boolean
  error: string | null
  load: () => Promise<void>
}

const messageFor = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'Unable to load organizations.')
    : 'An unexpected error occurred.'

export const useOrganizationsStore = create<OrganizationsState>((set) => ({
  organizations: [],
  loading: false,
  error: null,
  load: async () => {
    set({ loading: true, error: null })
    try {
      const organizations = await organizationsApi.listOrganizations()
      set({ organizations, loading: false })
    } catch (error) {
      set({ error: messageFor(error), loading: false })
    }
  },
}))
