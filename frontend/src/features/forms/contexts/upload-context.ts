import { createContext, useContext } from 'react'

export const UploadContext = createContext<string | undefined>(undefined)

export function useUploadUrl() {
  return useContext(UploadContext)
}
