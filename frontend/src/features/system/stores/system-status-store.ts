import axios from 'axios'
import { create } from 'zustand'

import {
  getBuildInfo,
  getLiveness,
  type BuildInfo,
  type HealthStatus,
} from '../api/system-api'

interface SystemStatusState {
  build: BuildInfo | null
  error: string | null
  health: HealthStatus | null
  isLoading: boolean
  load: () => Promise<void>
}

export const useSystemStatusStore = create<SystemStatusState>((set) => ({
  build: null,
  error: null,
  health: null,
  isLoading: false,
  load: async () => {
    set({ error: null, isLoading: true })
    try {
      const [health, build] = await Promise.all([getLiveness(), getBuildInfo()])
      set({ build, health, isLoading: false })
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? 'API is unavailable. Verify the backend configuration.'
        : 'Unable to load system status.'
      set({ error: message, isLoading: false })
    }
  },
}))
