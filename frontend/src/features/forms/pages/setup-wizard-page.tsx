import { useEffect } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'

import { Button } from '../../../shared/components/button'
import { PageHeader } from '../../../shared/components/page-header'
import { DownloadFormButton } from '../components/download-form-button'
import { SectionWizard } from '../components/section-wizard'
import {
  organizationFormSections,
  productFormSections,
  strategyFormSections,
} from '../form-field-schema'
import {
  organizationTemplate,
  productTemplate,
  strategyTemplate,
} from '../form-definitions'
import { useSetupStore } from '../stores/setup-store'

const organizationInitial = {
  identity: { name: '', website: 'https://', primary_contact_email: '' },
  ...organizationTemplate,
}
const productInitial = {
  identity: { name: '', kind: 'service' },
  ...productTemplate,
}
const strategyInitial = { ...strategyTemplate }

export function OrganizationWizardPage() {
  const store = useSetupStore()
  if (store.organizationId && !store.error) {
    return <Navigate replace to={`/orgs/${store.organizationId}/products/new`} />
  }
  return (
    <>
      <PageHeader
        title="New organization"
        subtitle="Complete the organization profile sections, then continue to a product."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { label: 'New' },
        ]}
        actions={
          <>
            <DownloadFormButton formKey="organization" />
            <Button asChild variant="ghost">
              <Link to="/orgs">Cancel</Link>
            </Button>
          </>
        }
      />
      <SectionWizard
        title="organization"
        sections={organizationFormSections}
        initialValue={organizationInitial}
        submitting={store.submitting}
        serverError={store.error}
        onSubmit={store.createOrganization}
      />
    </>
  )
}

export function ProductWizardPage() {
  const { orgId = '' } = useParams()
  const store = useSetupStore()
  if (store.productId && !store.error) {
    return <Navigate replace to={`/orgs/${orgId}/products/${store.productId}/sales-strategies/new`} />
  }
  return (
    <>
      <PageHeader
        title="New product or service"
        subtitle="Define the ICP profile, then create a sales strategy."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { label: 'Organization', to: `/orgs/${orgId}` },
          { label: 'New' },
        ]}
        actions={
          <>
            <DownloadFormButton formKey="product" />
            <Button asChild variant="ghost">
              <Link to={`/orgs/${orgId}`}>Cancel</Link>
            </Button>
          </>
        }
      />
      <SectionWizard
        title="product or service"
        sections={productFormSections}
        initialValue={productInitial}
        submitting={store.submitting}
        serverError={store.error}
        onSubmit={(value) => store.createProduct(orgId, value)}
      />
    </>
  )
}

export function StrategyWizardPage() {
  const { orgId = '', productId = '' } = useParams()
  const store = useSetupStore()
  const strategiesTab = `/orgs/${orgId}/products/${productId}`

  useEffect(() => {
    return () => {
      useSetupStore.getState().clearStrategyCreation()
    }
  }, [])

  if (store.strategyId) {
    return <Navigate replace to={strategiesTab} />
  }
  return (
    <>
      <PageHeader
        title="New sales strategy"
        subtitle="Strategy forms are immutable after creation — review targets carefully."
        breadcrumbs={[
          { label: 'Organizations', to: '/orgs' },
          { label: 'Organization', to: `/orgs/${orgId}` },
          {
            label: 'Product',
            to: `/orgs/${orgId}/products/${productId}`,
          },
          {
            label: 'Strategies',
            to: strategiesTab,
          },
          { label: 'New' },
        ]}
        actions={
          <>
            <DownloadFormButton formKey="sales-strategy" />
            <Button asChild variant="ghost">
              <Link to={strategiesTab}>Cancel</Link>
            </Button>
          </>
        }
      />
      <SectionWizard
        title="sales strategy"
        sections={strategyFormSections}
        initialValue={strategyInitial}
        submitting={store.submitting}
        serverError={store.error}
        onSubmit={(value) => store.createStrategy(productId, value)}
      />
    </>
  )
}
