import axios from 'axios'
import { create } from 'zustand'

import { salesStrategyApi, type SalesStrategy } from '../api/sales-strategy-api'

interface StrategiesListState {
  strategies: SalesStrategy[]
  loading: boolean
  error: string | null
  load: (productId: string) => Promise<void>
}

const messageFor = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'Unable to load sales strategies for this product.')
    : 'An unexpected error occurred.'

export const useStrategiesListStore = create<StrategiesListState>((set) => ({
  strategies: [],
  loading: false,
  error: null,
  load: async (productId) => {
    set({ loading: true, error: null, strategies: [] })
    try {
      const strategies = await salesStrategyApi.listStrategies(productId)
      set({ strategies, loading: false })
    } catch (error) {
      set({ error: messageFor(error), loading: false })
    }
  },
}))
