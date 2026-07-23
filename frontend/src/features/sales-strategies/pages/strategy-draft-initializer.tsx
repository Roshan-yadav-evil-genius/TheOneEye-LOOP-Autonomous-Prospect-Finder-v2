import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { salesStrategyApi } from '../api/sales-strategy-api'

export function StrategyDraftInitializer() {
  const { orgId = '', productId = '' } = useParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const createdRef = useRef(false)

  useEffect(() => {
    if (!productId || createdRef.current) return
    createdRef.current = true

    void salesStrategyApi
      .createStrategy(productId, {})
      .then((created) => {
        navigate(
          `/orgs/${orgId}/products/${productId}/sales-strategies/${created.id}/edit`,
          { replace: true }
        )
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to create sales strategy draft.')
      })
  }, [orgId, productId, navigate])

  if (error) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return <p className="muted">Creating sales strategy draft…</p>
}
