import axios from 'axios'
import { create } from 'zustand'

import { productsApi, type Product } from '../api/products-api'

interface ProductDetailState {
  product: Product | null
  loading: boolean
  submitting: boolean
  error: string | null
  saved: boolean
  load: (productId: string) => Promise<void>
  save: (productId: string, value: Record<string, unknown>) => Promise<void>
  reset: () => void
}

const messageFor = (error: unknown, fallback: string) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? fallback)
    : fallback

export const useProductDetailStore = create<ProductDetailState>((set) => ({
  product: null,
  loading: false,
  submitting: false,
  error: null,
  saved: false,
  reset: () => set({ product: null, loading: false, submitting: false, error: null, saved: false }),
  load: async (productId) => {
    set({ loading: true, error: null, saved: false })
    try {
      const product = await productsApi.getProduct(productId)
      set({ product, loading: false })
    } catch (error) {
      set({ error: messageFor(error, 'Unable to load product.'), loading: false })
    }
  },
  save: async (productId, value) => {
    set({ submitting: true, error: null, saved: false })
    try {
      const { identity: identityValue, ...icpForm } = value
      const identity = identityValue as { name: string; kind: 'product' | 'service' }
      const product = await productsApi.updateProductProfile(productId, {
        form: { form_version: '2.0', ...icpForm },
        name: identity.name,
        kind: identity.kind,
      })
      const result = await productsApi.validateProduct(productId)
      set({
        product,
        submitting: false,
        saved: result.valid,
        error: result.valid ? null : `Missing: ${result.missing_sections.join(', ')}`,
      })
    } catch (error) {
      set({
        error: messageFor(error, 'Unable to save product profile.'),
        submitting: false,
      })
    }
  },
}))
