import { create } from 'zustand'

import {
  type ProcessStatus,
  type Whiteboard,
  salesStrategyApi,
} from '../api/sales-strategy-api'

interface ProcessState {
  status: ProcessStatus | null
  whiteboard: Whiteboard | null
  loading: boolean
  load: (strategyId: string, role: string) => Promise<void>
  start: (strategyId: string, role: string) => Promise<void>
  stop: (strategyId: string, role: string) => Promise<void>
  saveWhiteboard: (strategyId: string, role: string, content: string) => Promise<void>
}

const createProcessStore = () =>
  create<ProcessState>((set, get) => ({
    status: null,
    whiteboard: null,
    loading: false,
    load: async (strategyId, role) => {
      set({ loading: true })
      const [status, whiteboard] = await Promise.all([
        salesStrategyApi.processStatus(strategyId, role),
        salesStrategyApi.getWhiteboard(strategyId, role),
      ])
      set({ status, whiteboard, loading: false })
    },
    start: async (strategyId, role) => {
      set({ status: await salesStrategyApi.startProcess(strategyId, role) })
    },
    stop: async (strategyId, role) => {
      set({ status: await salesStrategyApi.stopProcess(strategyId, role) })
    },
    saveWhiteboard: async (strategyId, role, content) => {
      set({
        whiteboard: await salesStrategyApi.updateWhiteboard(strategyId, role, content),
      })
      await get().load(strategyId, role)
    },
  }))

export const useCompanyFinderProcessStore = createProcessStore()
export const useContactFinderProcessStore = createProcessStore()
