import { Navigate, useParams } from 'react-router-dom'

/** Legacy products list route — products now live on the organization Products tab. */
export function ProductsPage() {
  const { orgId = '' } = useParams()
  return <Navigate replace to={`/orgs/${orgId}`} />
}
