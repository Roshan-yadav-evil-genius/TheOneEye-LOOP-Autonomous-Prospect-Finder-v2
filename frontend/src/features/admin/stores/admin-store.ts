import axios from 'axios'
import { create } from 'zustand'

import {
  adminApi,
  type AuditEvent,
  type DeadLetter,
  type JobRun,
  type Schedule,
} from '../api/admin-api'

interface AdminState {
  audit: AuditEvent[]
  deadLetters: DeadLetter[]
  jobs: JobRun[]
  schedules: Schedule[]
  error: string | null
  loading: boolean
  load: () => Promise<void>
  replay: (id: string) => Promise<void>
  discard: (id: string) => Promise<void>
}

const message = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'Admin request failed.')
    : 'Admin request failed.'

export const useAdminStore = create<AdminState>((set, get) => ({
  audit: [],
  deadLetters: [],
  jobs: [],
  schedules: [],
  error: null,
  loading: false,
  load: async () => {
    set({ error: null, loading: true })
    try {
      const [audit, deadLetters, jobs, schedules] = await Promise.all([
        adminApi.audit(),
        adminApi.deadLetters(),
        adminApi.jobs(),
        adminApi.schedules(),
      ])
      set({ audit, deadLetters, jobs, schedules, loading: false })
    } catch (error) {
      set({ error: message(error), loading: false })
    }
  },
  replay: async (id) => {
    try {
      await adminApi.replay(id)
      await get().load()
    } catch (error) {
      set({ error: message(error) })
    }
  },
  discard: async (id) => {
    try {
      await adminApi.discard(id)
      await get().load()
    } catch (error) {
      set({ error: message(error) })
    }
  },
}))
