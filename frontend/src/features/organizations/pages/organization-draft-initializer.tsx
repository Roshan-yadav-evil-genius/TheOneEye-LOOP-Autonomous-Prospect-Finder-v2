import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { organizationsApi } from '../api/organizations-api'

export function OrganizationDraftInitializer() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const createdRef = useRef(false)

  useEffect(() => {
    if (createdRef.current) return
    createdRef.current = true

    void organizationsApi
      .createOrganization({})
      .then((created) => {
        navigate(`/orgs/${created.id}/edit`, { replace: true })
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to create organization draft.')
      })
  }, [navigate])

  if (error) {
    return <p role="alert" className="error-banner">{error}</p>
  }

  return <p className="muted">Creating organization draft…</p>
}
