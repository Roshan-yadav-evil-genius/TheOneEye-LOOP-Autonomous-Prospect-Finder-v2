import { Navigate, useParams } from 'react-router-dom'

/** Legacy edit route — product profile editing lives on the Details tab. */
export function ProductEditPage() {
  const { orgId = '', productId = '' } = useParams()
  return (
    <Navigate
      replace
      to={`/orgs/${orgId}/products/${productId}?tab=details&mode=edit`}
    />
  )
}
