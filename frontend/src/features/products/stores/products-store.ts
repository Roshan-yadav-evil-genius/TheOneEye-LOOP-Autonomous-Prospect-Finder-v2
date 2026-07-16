import axios from 'axios'
import { create } from 'zustand'

import { productsApi, type Product } from '../api/products-api'

interface ProductsState {
  products: Product[]
  loading: boolean
  error: string | null
  load: (organizationId: string) => Promise<void>
}

const messageFor = (error: unknown) =>
  axios.isAxiosError<{ message?: string }>(error)
    ? (error.response?.data.message ?? 'Unable to load products for this organization.')
    : 'An unexpected error occurred.'

export const useProductsStore = create<ProductsState>((set) => ({
  products: [],
  loading: false,
  error: null,
  load: async (organizationId) => {
    set({ loading: true, error: null })
    try {
      const products = await productsApi.listProducts(organizationId)
      set({ products, loading: false })
    } catch (error) {
      set({ error: messageFor(error), loading: false })
    }
  },
}))
