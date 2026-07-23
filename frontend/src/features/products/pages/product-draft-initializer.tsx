import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { productsApi } from '../api/products-api'

export function ProductDraftInitializer() {
  const { orgId = '' } = useParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const createdRef = useRef(false)

  useEffect(() => {
    if (!orgId || createdRef.current) return
    createdRef.current = true

    void productsApi
      .createProduct(orgId, {})
      .then((created) => {
        navigate(`/orgs/${orgId}/products/${created.id}/edit`, { replace: true })
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to create product draft.')
      })
  }, [orgId, navigate])

  if (error) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return <p className="muted">Creating product draft…</p>
}
