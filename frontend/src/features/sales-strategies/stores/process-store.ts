import { create } from 'zustand'

import {
  type ProcessStatus,
  salesStrategyApi,
} from '../api/sales-strategy-api'

interface ProcessState {
  status: ProcessStatus | null
  loading: boolean
  load: (strategyId: string, role: string) => Promise<void>
  start: (strategyId: string, role: string) => Promise<void>
  stop: (strategyId: string, role: string) => Promise<void>
}

const createProcessStore = () =>
  create<ProcessState>((set) => ({
    status: null,
    loading: false,
    load: async (strategyId, role) => {
      set({ loading: true })
      const status = await salesStrategyApi.processStatus(strategyId, role)
      set({ status, loading: false })
    },
    start: async (strategyId, role) => {
      set({ status: await salesStrategyApi.startProcess(strategyId, role) })
    },
    stop: async (strategyId, role) => {
      set({ status: await salesStrategyApi.stopProcess(strategyId, role) })
    },
  }))

export const useCompanyFinderProcessStore = createProcessStore()
export const useContactFinderProcessStore = createProcessStore()

