import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { Link, NavLink, useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import { PageHeader } from '../../../shared/components/page-header'
import { useWorkspaceContextStore } from '../stores/workspace-context-store'

const tabs = [
  ['companies', 'Company'],
  ['company-finder', 'Company finder'],
  ['contact-finder', 'Contact finder'],
  ['threads', 'Threads'],
  ['details', 'Details'],
  ['chat', 'Chat'],
] as const

export function WorkspaceShell({
  children,
  pageTitle,
  pageSubtitle,
  actions,
}: {
  children: ReactNode
  /** Optional page-level title override under the strategy name. */
  pageTitle?: string
  pageSubtitle?: string
  actions?: ReactNode
}) {
  const { orgId = '', strategyId = '', companyId } = useParams()
  const { bundle, load, loading } = useWorkspaceContextStore()
  const base = `/orgs/${orgId}/sales-strategies/${strategyId}`
  const showWorkspaceTabs = !companyId

  useEffect(() => {
    if (strategyId) void load(strategyId)
  }, [load, strategyId])

  const org = bundle?.organization
  const product = bundle?.product
  const strategy = bundle?.sales_strategy
  const strategyName = strategy?.name ?? (loading ? 'Loading…' : 'Sales strategy')

  const breadcrumbs = [
    { label: 'Organizations', to: '/orgs' },
    ...(org
      ? [{ 
          label: org.name, 
          to: `/orgs/${org.id}`,
          thumbnailUrl: (org as any).thumbnail_url,
          fallbackThumbnailUrl: '/static/org_placeholder.png'
        }]
      : [{ label: 'Organization', to: `/orgs/${orgId}` }]),
    ...(org && product
      ? [{ 
          label: product.name, 
          to: `/orgs/${org.id}/products/${product.id}`,
          thumbnailUrl: (product as any).thumbnail_url,
          fallbackThumbnailUrl: '/static/product_service_placeholder.png'
        }]
      : []),
    {
      label: strategyName,
      to: companyId ? `${base}/companies` : undefined,
      thumbnailUrl: strategy ? (strategy as any).thumbnail_url : null,
      fallbackThumbnailUrl: '/static/strategy_placeholder.png'
    },
    ...(companyId
      ? [
          { label: 'Company', to: `${base}/companies` },
          { label: pageTitle ?? 'Company' },
        ]
      : []),
  ]

  return (
    <>
      <PageHeader
        title={pageTitle ?? strategyName}
        subtitle={
          pageSubtitle ??
          (product
            ? `${product.name} · operator workspace`
            : 'Strategy details, companies, finder processes, and threads.')
        }
        breadcrumbs={breadcrumbs}
        actions={
          actions ?? (
            <Button asChild variant="ghost">
              <Link to={companyId ? `${base}/companies` : org ? `/orgs/${org.id}` : '/orgs'}>
                {companyId ? '← Company' : '← Organization'}
              </Link>
            </Button>
          )
        }
      />
      {showWorkspaceTabs ? (
        <nav className="workspace-tabs" aria-label="Sales strategy">
          {tabs.map(([path, label]) => (
            <NavLink
              key={path}
              to={`${base}/${path}`}
              className={({ isActive }) => (isActive ? 'workspace-tab active' : 'workspace-tab')}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      ) : null}
      {children}
    </>
  )
}
