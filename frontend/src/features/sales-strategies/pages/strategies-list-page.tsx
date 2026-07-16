import { Navigate, useParams } from 'react-router-dom'

/** Legacy strategies list — strategies now live on the product Strategies tab. */
export function StrategiesListPage() {
  const { orgId = '', productId = '' } = useParams()
  return <Navigate replace to={`/orgs/${orgId}/products/${productId}`} />
}
