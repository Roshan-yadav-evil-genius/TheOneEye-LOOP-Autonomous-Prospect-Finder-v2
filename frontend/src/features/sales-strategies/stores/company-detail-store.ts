import axios from 'axios'
import { create } from 'zustand'

import {
  type CompanyDetail,
  type OutreachUpdate,
  type RegisterContactRequest,
  salesStrategyApi,
} from '../api/sales-strategy-api'

interface CompanyDetailState {
  detail: CompanyDetail | null
  loading: boolean
  error: string | null
  savingProfile: boolean
  savingContact: boolean
  drafts: Record<string, OutreachUpdate>
  load: (strategyId: string, companyId: string) => Promise<void>
  reset: () => void
  setDraft: (prospectProfileId: string, patch: OutreachUpdate) => void
  saveOutreach: (
    strategyId: string,
    companyId: string,
    prospectProfileId: string,
  ) => Promise<void>
  updateProfile: (
    strategyId: string,
    companyId: string,
    profile: Record<string, unknown>,
  ) => Promise<void>
  registerContact: (
    strategyId: string,
    companyId: string,
    payload: RegisterContactRequest,
  ) => Promise<string | null>
  blacklistProspect: (
    strategyId: string,
    companyId: string,
    prospectProfileId: string,
    reason: string,
  ) => Promise<void>
  unblacklistProspect: (
    strategyId: string,
    companyId: string,
    prospectProfileId: string,
  ) => Promise<void>
  blacklistCompany: (strategyId: string, companyId: string, reason: string) => Promise<void>
  unblacklistCompany: (strategyId: string, companyId: string) => Promise<void>
}

const messageFor = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'The requested action could not be completed.')
    : 'An unexpected error occurred.'

const initialState = {
  detail: null as CompanyDetail | null,
  loading: false,
  error: null as string | null,
  savingProfile: false,
  savingContact: false,
  drafts: {} as Record<string, OutreachUpdate>,
}

export const useCompanyDetailStore = create<CompanyDetailState>((set, get) => ({
  ...initialState,
  load: async (strategyId, companyId) => {
    set({ loading: true, error: null })
    try {
      const detail = await salesStrategyApi.getCompany(strategyId, companyId)
      set({ detail, loading: false, drafts: {} })
    } catch (error) {
      set({ error: messageFor(error), loading: false })
    }
  },
  reset: () => set(initialState),
  setDraft: (prospectProfileId, patch) => {
    set((state) => ({
      drafts: {
        ...state.drafts,
        [prospectProfileId]: { ...state.drafts[prospectProfileId], ...patch },
      },
    }))
  },
  saveOutreach: async (strategyId, companyId, prospectProfileId) => {
    const draft = get().drafts[prospectProfileId] ?? {}
    if (draft.response_sentiment === 'negative' && !draft.response_negative_reason?.trim()) {
      set({ error: 'Negative response requires a reason. Your draft is preserved.' })
      return
    }
    try {
      set({ error: null })
      await salesStrategyApi.updateOutreach(strategyId, companyId, prospectProfileId, draft)
      await get().load(strategyId, companyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  updateProfile: async (strategyId, companyId, profile) => {
    set({ savingProfile: true, error: null })
    try {
      const detail = await salesStrategyApi.updateCompanyProfile(strategyId, companyId, {
        profile,
      })
      set({ detail, savingProfile: false })
    } catch (error) {
      set({ error: messageFor(error), savingProfile: false })
    }
  },
  registerContact: async (strategyId, companyId, payload) => {
    set({ savingContact: true, error: null })
    try {
      const result = await salesStrategyApi.registerContact(strategyId, companyId, payload)
      await get().load(strategyId, companyId)
      set({ savingContact: false })
      if (result.message === 'registered') return null
      if (result.message === 'already_in_strategy') {
        return 'This contact is already registered for this strategy.'
      }
      if (result.message === 'already_in_db') {
        return 'Contact exists globally and was linked to this strategy.'
      }
      if (result.message === 'blacklisted') {
        return 'Contact was registered but is blacklisted.'
      }
      return null
    } catch (error) {
      set({ error: messageFor(error), savingContact: false })
      return 'Registration failed.'
    }
  },
  blacklistProspect: async (strategyId, companyId, prospectProfileId, reason) => {
    try {
      set({ error: null })
      await salesStrategyApi.blacklistProspect(
        strategyId,
        companyId,
        prospectProfileId,
        reason,
      )
      await get().load(strategyId, companyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  unblacklistProspect: async (strategyId, companyId, prospectProfileId) => {
    try {
      set({ error: null })
      await salesStrategyApi.unblacklistProspect(strategyId, companyId, prospectProfileId)
      await get().load(strategyId, companyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  blacklistCompany: async (strategyId, companyId, reason) => {
    try {
      set({ error: null })
      await salesStrategyApi.blacklistCompany(strategyId, companyId, reason)
      await get().load(strategyId, companyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  unblacklistCompany: async (strategyId, companyId) => {
    try {
      set({ error: null })
      await salesStrategyApi.unblacklistCompany(strategyId, companyId)
      await get().load(strategyId, companyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
}))
