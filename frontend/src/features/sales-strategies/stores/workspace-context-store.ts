import axios from 'axios'
import { create } from 'zustand'

import type { components } from '../../../shared/api/generated/schema'
import { salesStrategyApi } from '../api/sales-strategy-api'

export type SalesStrategyBundle = components['schemas']['SalesStrategyBundle']

interface WorkspaceContextState {
  bundle: SalesStrategyBundle | null
  strategyId: string | null
  loading: boolean
  error: string | null
  load: (strategyId: string) => Promise<void>
  reset: () => void
}

const message = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'Unable to load workspace context.')
    : 'Unable to load workspace context.'

export const useWorkspaceContextStore = create<WorkspaceContextState>((set, get) => ({
  bundle: null,
  strategyId: null,
  loading: false,
  error: null,
  load: async (strategyId) => {
    if (get().strategyId === strategyId && get().bundle) return
    const switching = get().strategyId !== strategyId
    set({
      loading: true,
      error: null,
      strategyId,
      bundle: switching ? null : get().bundle,
    })
    try {
      const bundle = await salesStrategyApi.getBundle(strategyId)
      if (get().strategyId !== strategyId) return
      set({ bundle, loading: false })
    } catch (error) {
      if (get().strategyId !== strategyId) return
      set({ error: message(error), loading: false, bundle: null })
    }
  },
  reset: () => set({ bundle: null, strategyId: null, loading: false, error: null }),
}))
