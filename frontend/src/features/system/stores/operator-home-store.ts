import axios from 'axios'
import { create } from 'zustand'

import { adminApi } from '../../admin/api/admin-api'
import { organizationsApi, type Organization } from '../../organizations/api/organizations-api'
import { productsApi } from '../../products/api/products-api'
import { salesStrategyApi } from '../../sales-strategies/api/sales-strategy-api'
import {
  getBuildInfo,
  getLiveness,
  type BuildInfo,
  type HealthStatus,
} from '../api/system-api'

export interface RunningFinder {
  strategyId: string
  strategyName: string
  orgId: string
  orgName: string
  productId: string
  role: 'company-finder' | 'contact-finder'
  state: string
}

interface OperatorHomeState {
  build: BuildInfo | null
  health: HealthStatus | null
  organizations: Organization[]
  incompleteProfiles: Organization[]
  runningFinders: RunningFinder[]
  dlqCount: number
  activeJobs: number
  error: string | null
  loading: boolean
  load: () => Promise<void>
}

const message = (error: unknown) =>
  axios.isAxiosError(error)
    ? 'API is unavailable. Verify the backend configuration.'
    : 'Unable to load operator home.'

export const useOperatorHomeStore = create<OperatorHomeState>((set) => ({
  build: null,
  health: null,
  organizations: [],
  incompleteProfiles: [],
  runningFinders: [],
  dlqCount: 0,
  activeJobs: 0,
  error: null,
  loading: false,
  load: async () => {
    set({ error: null, loading: true })
    try {
      const [health, build, organizations, jobs, deadLetters] = await Promise.all([
        getLiveness(),
        getBuildInfo(),
        organizationsApi.listOrganizations(),
        adminApi.jobs().catch(() => []),
        adminApi.deadLetters().catch(() => []),
      ])

      const incompleteProfiles = organizations.filter((org) => !org.profile_validated)
      const activeJobs = jobs.filter(
        (job) => !['completed', 'cancelled'].includes(job.status),
      ).length
      const dlqCount = deadLetters.filter((item) => item.replay_state === 'pending').length

      // Thin fan-out: sample recent orgs' first product/strategy for running finders.
      const runningFinders: RunningFinder[] = []
      const sampleOrgs = organizations.slice(0, 5)
      await Promise.all(
        sampleOrgs.map(async (org) => {
          try {
            const products = await productsApi.listProducts(org.id)
            const product = products[0]
            if (!product) return
            const strategies = await salesStrategyApi.listStrategies(product.id)
            const strategy = strategies[0]
            if (!strategy) return
            const [companyStatus, contactStatus] = await Promise.all([
              salesStrategyApi.processStatus(strategy.id, 'company-finder').catch(() => null),
              salesStrategyApi.processStatus(strategy.id, 'contact-finder').catch(() => null),
            ])
            if (companyStatus?.actual_state === 'running') {
              runningFinders.push({
                strategyId: strategy.id,
                strategyName: strategy.name,
                orgId: org.id,
                orgName: org.name,
                productId: product.id,
                role: 'company-finder',
                state: companyStatus.actual_state,
              })
            }
            if (contactStatus?.actual_state === 'running') {
              runningFinders.push({
                strategyId: strategy.id,
                strategyName: strategy.name,
                orgId: org.id,
                orgName: org.name,
                productId: product.id,
                role: 'contact-finder',
                state: contactStatus.actual_state,
              })
            }
          } catch {
            // Skip org if product/strategy fan-out fails.
          }
        }),
      )

      set({
        build,
        health,
        organizations: organizations.slice(0, 8),
        incompleteProfiles: incompleteProfiles.slice(0, 8),
        runningFinders,
        dlqCount,
        activeJobs,
        loading: false,
      })
    } catch (error) {
      set({ error: message(error), loading: false })
    }
  },
}))
