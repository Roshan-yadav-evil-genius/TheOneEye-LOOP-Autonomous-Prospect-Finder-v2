import { create } from 'zustand'

import {
  type AgentRun,
  type ThreadSnapshot,
  salesStrategyApi,
} from '../api/sales-strategy-api'

interface ThreadsState {
  threads: AgentRun[]
  snapshot: ThreadSnapshot | null
  load: (strategyId: string) => Promise<void>
  open: (strategyId: string, threadId: string) => Promise<void>
}

export const useThreadsStore = create<ThreadsState>((set) => ({
  threads: [],
  snapshot: null,
  load: async (strategyId) => {
    set({ threads: await salesStrategyApi.getThreads(strategyId) })
  },
  open: async (strategyId, threadId) => {
    set({ snapshot: await salesStrategyApi.getSnapshot(strategyId, threadId) })
  },
}))
