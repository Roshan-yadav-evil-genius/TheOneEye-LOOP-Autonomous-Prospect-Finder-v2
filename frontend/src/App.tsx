import { Navigate, Route, Routes } from 'react-router-dom'

import { AdminPage } from './features/admin/pages/admin-page'
import { OrganizationDetailPage } from './features/organizations/pages/organization-detail-page'
import { OrganizationsPage } from './features/organizations/pages/organizations-page'
import { OrganizationEditPage } from './features/organizations/pages/organization-edit-page'
import { OrganizationDraftInitializer } from './features/organizations/pages/organization-draft-initializer'

import { ProductDetailPage } from './features/products/pages/product-detail-page'
import { ProductsPage } from './features/products/pages/products-page'
import { ProductEditPage } from './features/products/pages/product-edit-page'
import { ProductDraftInitializer } from './features/products/pages/product-draft-initializer'

import { CompanyDetailPage } from './features/sales-strategies/pages/company-detail-page'
import { EffortDetailPage } from './features/sales-strategies/pages/effort-detail-page'
import { ProcessPage } from './features/sales-strategies/pages/process-page'
import { RecordsPage } from './features/sales-strategies/pages/records-page'
import { StrategiesListPage } from './features/sales-strategies/pages/strategies-list-page'
import { StrategyPage } from './features/sales-strategies/pages/strategy-page'
import { StrategyEditPage } from './features/sales-strategies/pages/strategy-edit-page'
import { StrategyDraftInitializer } from './features/sales-strategies/pages/strategy-draft-initializer'
import { ThreadsPage } from './features/sales-strategies/pages/threads-page'

import { GlobalThreadsPage } from './features/system/pages/global-threads-page'
import { ThreadChatPage } from './features/system/pages/thread-chat-page'
import { OperatorHomePage } from './features/system/components/operator-home-page'
import { PageShell } from './shared/components/page-shell'

function App() {
  return (
    <PageShell>
      <Routes>
        <Route index element={<OperatorHomePage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/threads" element={<GlobalThreadsPage />} />
        <Route path="/threads/:threadId" element={<ThreadChatPage />} />
        
        {/* Organizations */}
        <Route path="/orgs" element={<OrganizationsPage />} />
        <Route path="/orgs/new" element={<OrganizationDraftInitializer />} />
        <Route path="/orgs/:orgId" element={<OrganizationDetailPage />} />
        <Route path="/orgs/:orgId/edit" element={<OrganizationEditPage />} />
        
        {/* Products */}
        <Route path="/orgs/:orgId/products" element={<ProductsPage />} />
        <Route path="/orgs/:orgId/products/new" element={<ProductDraftInitializer />} />
        <Route path="/orgs/:orgId/products/:productId" element={<ProductDetailPage />} />
        <Route path="/orgs/:orgId/products/:productId/edit" element={<ProductEditPage />} />
        
        {/* Strategies */}
        <Route
          path="/orgs/:orgId/products/:productId/sales-strategies"
          element={<StrategiesListPage />}
        />
        <Route
          path="/orgs/:orgId/products/:productId/sales-strategies/new"
          element={<StrategyDraftInitializer />}
        />
        <Route
          path="/orgs/:orgId/products/:productId/sales-strategies/:strategyId/edit"
          element={<StrategyEditPage />}
        />
        
        {/* Strategy Context Routes */}
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId"
          element={<Navigate replace to="companies" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/details"
          element={<StrategyPage />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/strategy"
          element={<Navigate replace to="../details" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/companies"
          element={<RecordsPage />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/records"
          element={<Navigate replace to="../companies" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/company-finder"
          element={<ProcessPage role="company-finder" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/company-finder/effort/:effortSeq"
          element={<EffortDetailPage role="company-finder" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/contact-finder"
          element={<ProcessPage role="contact-finder" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/contact-finder/effort/:effortSeq"
          element={<EffortDetailPage role="contact-finder" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/companies/:companyId/contact-finder/effort/:effortSeq"
          element={<EffortDetailPage role="contact-finder" />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/threads"
          element={<ThreadsPage />}
        />
        <Route
          path="/orgs/:orgId/sales-strategies/:strategyId/companies/:companyId"
          element={<CompanyDetailPage />}
        />
        
        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </PageShell>
  )
}

export default App
