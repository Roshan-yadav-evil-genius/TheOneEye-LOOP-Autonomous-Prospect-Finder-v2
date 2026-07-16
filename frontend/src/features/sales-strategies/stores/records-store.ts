import axios from 'axios'
import { create } from 'zustand'

import {
  type CompanySummary,
  type Progress,
  type RegisterCompanyRequest,
  salesStrategyApi,
} from '../api/sales-strategy-api'

interface RecordsState {
  companies: CompanySummary[]
  progress: Progress | null
  loading: boolean
  error: string | null
  load: (strategyId: string) => Promise<void>
  register: (strategyId: string, payload: RegisterCompanyRequest) => Promise<void>
  validate: (strategyId: string, companyId: string) => Promise<void>
  blacklist: (strategyId: string, companyId: string, reason: string) => Promise<void>
  unblacklist: (strategyId: string, companyId: string) => Promise<void>
}

const messageFor = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'The requested action could not be completed.')
    : 'An unexpected error occurred.'

export const useRecordsStore = create<RecordsState>((set, get) => ({
  companies: [],
  progress: null,
  loading: false,
  error: null,
  load: async (strategyId) => {
    set({ loading: true, error: null })
    try {
      const [companies, progress] = await Promise.all([
        salesStrategyApi.getRecords(strategyId),
        salesStrategyApi.getProgress(strategyId),
      ])
      set({ companies, progress, loading: false })
    } catch (error) {
      set({ error: messageFor(error), loading: false })
    }
  },
  register: async (strategyId, payload) => {
    try {
      set({ error: null })
      await salesStrategyApi.registerCompany(strategyId, payload)
      await get().load(strategyId)
    } catch (error) {
      set({ error: messageFor(error) })
      throw error
    }
  },
  validate: async (strategyId, companyId) => {
    try {
      await salesStrategyApi.validateCompany(strategyId, companyId)
      await get().load(strategyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  blacklist: async (strategyId, companyId, reason) => {
    try {
      await salesStrategyApi.blacklistCompany(strategyId, companyId, reason)
      await get().load(strategyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
  unblacklist: async (strategyId, companyId) => {
    try {
      await salesStrategyApi.unblacklistCompany(strategyId, companyId)
      await get().load(strategyId)
    } catch (error) {
      set({ error: messageFor(error) })
    }
  },
}))
