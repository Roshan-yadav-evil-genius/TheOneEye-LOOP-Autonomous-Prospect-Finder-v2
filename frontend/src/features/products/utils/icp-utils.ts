import { productTemplate } from '../../forms/form-definitions'

export function toProductFormValue(product: {
  name: string
  kind: string
  icp_form: Record<string, unknown>
}) {
  const icpForm = product.icp_form ?? {}
  const rawIcp = (icpForm.icp as Record<string, unknown>) || {}
  const templateIcp = (productTemplate.icp as Record<string, unknown>) || {}

  return {
    identity: {
      name: product.name,
      kind: product.kind,
      thumbnail_url: (product as any).thumbnail_url,
    },
    ...productTemplate,
    ...icpForm,
    icp: {
      ...templateIcp,
      ...rawIcp,
      industries: {
        ...((templateIcp.industries as Record<string, unknown>) || {}),
        ...((rawIcp.industries as Record<string, unknown>) || {}),
      },
      company_size: {
        ...((templateIcp.company_size as Record<string, unknown>) || {}),
        ...((rawIcp.company_size as Record<string, unknown>) || {}),
      },
      geography: {
        ...((templateIcp.geography as Record<string, unknown>) || {}),
        ...((rawIcp.geography as Record<string, unknown>) || {}),
      },
    },
  }
}
