# Frontend Plan

## Objectives and scope

Build the React operator application for product/service setup, sales strategy creation, the five-tab sales strategy workspace, company drill-down, human validation/outreach, agent process control, whiteboards, progress, and thread snapshots.

**Form wizards:** [form/README.md](form/README.md) — section counts, gates, and read-only Strategy tab rules.

## Functional requirements

- Organization profile wizard ([organization_form.md](form/organization_form.md) — 21 sections).
- Product/service profile wizard ([service_form.md](form/service_form.md) — 18 sections).
- Sales Strategy create wizard matching **Sales Strategy** `SalesStrategy.sales_strategy_form` v2.0 ([sales_strategy_form.md](form/sales_strategy_form.md) — pillars table + §1–20); Strategy tab read-only after create.
- Sales Strategy workspace tabs:
  1. Strategy (default)
  2. Records Viewer
  3. Company Finder Process
  4. Contact Finder Process
  5. Threads
- Company detail page with all company information and registered prospects.
- Mark-valid / **blacklist** (company and prospect, with reason); fixed per-company contact quota (no +/−).
- Process play/pause, execution counts, logs, status, and one whiteboard per process.
- All sales strategy threads, linked/unlinked filters, and embedded snapshot viewer.

## Non-functional requirements

- TypeScript strict and backend-generated data structures.
- Axios for all HTTP and Zustand with one domain concern per store.
- WCAG 2.1 AA on the **dark-default** theme; light mode follows separate contrast pass.
- Polling must pause when hidden and avoid duplicate process requests.
- Action errors must preserve operator input and provide recovery guidance.

## Architecture and design decisions

- React 18+, Vite, React Router nested sales_strategy routes.
- **Approved UI theme:** dark-first LOOP operator console — see [UI theme and design system](15-ui-theme-and-design-system.md).
- Radix UI + Tailwind CSS with semantic design tokens (no hard-coded palette in features).
- Global shell: top nav, page header, horizontal tabs, main content (~70%), optional whiteboard side rail (~30%).
- Feature-first modules and reusable data-table/form primitives from the shared design system.
- React Hook Form + Zod schemas aligned to generated OpenAPI types.
- Server calls in feature API modules; components never call Axios directly.
- Optimistic UI only for low-risk toggles; funnel/process commands wait for server acknowledgement.
- Company detail is a drill-down route, not a sixth tab.

## Data models

Frontend consumes generated:

- Product/profile and SalesStrategy/form DTOs.
- `SalesStrategyCompanySummary`, `CompanyDetail` (global Company + optional CompanyProfile + strategy state), `ProspectProfileRead`, `SalesStrategyProspectRead`.
- `ProcessStatus`, `ProcessLogEntry`, `WhiteboardRead`.
- `AgentRunSummary`, `ThreadSnapshot`, `ProgressRead`.

Zustand slices:

- `useProductStore`, `useSalesStrategyStore`
- `useRecordsViewerStore`
- `useCompanyFinderProcessStore`, `useContactFinderProcessStore`
- `useCompanyDetailStore`, `useThreadsStore`, `useProgressStore`

## APIs and interfaces

Routes (URL-based org context):

```text
/orgs/:orgId/products
/orgs/:orgId/products/:productId/profile
/orgs/:orgId/products/:productId/sales-strategies/new
/orgs/:orgId/sales-strategies/:id/strategy
/orgs/:orgId/sales-strategies/:id/records
/orgs/:orgId/sales-strategies/:id/company-finder
/orgs/:orgId/sales-strategies/:id/contact-finder
/orgs/:orgId/sales-strategies/:id/threads
/orgs/:orgId/sales-strategies/:id/threads/snapshots/:threadId
/orgs/:orgId/sales-strategies/:id/companies/:companyId
```

Interfaces are generated from the API plan; domain-specific Axios modules own calls and response normalization.

## Target directory structure

```text
loop/apps/web/src/
├── app/
├── features/
│   ├── products/
│   ├── sales-strategies/
│   ├── records-viewer/
│   ├── company-detail/
│   ├── company-finder-process/
│   ├── contact-finder-process/
│   ├── threads/
│   └── progress/
├── shared/
│   ├── api/
│   ├── components/       # design system — see 15-ui-theme-and-design-system.md
│   ├── styles/           # tokens.css, globals, tailwind theme
│   ├── hooks/
│   └── stores/
└── assets/
```

## Milestones and implementation tasks

### M1 — Shell, theme, and forms

- Implement design tokens, ThemeProvider, PageShell (global nav + theme toggle), Tabs, Button, Card, and form primitives per [UI theme plan](15-ui-theme-and-design-system.md).
- Add routing, Axios client, generated types, error boundaries.
- Implement product/profile and sales_strategy-create wizards using themed form layout.

### M2 — Manual sales_strategy workflow

- Implement Strategy and Records Viewer using **MetricTile + SearchField + DataTable** pattern.
- Add funnel/queue badges (amber info, coral blocked/blacklist, blue-violet progress).
- Implement Company detail with global identity, optional enrichment placeholders, strategy-specific funnel/quota, and `SalesStrategyProspect` outreach table.

### M3 — Process pages

- Add Company/Contact Finder pages with **Control | Whiteboard** sub-tabs.
- Control sub-tab: play/pause (amber primary), execution metric tiles, log DataTable.
- Whiteboard sub-tab: markdown panel (same visual language as process side rail).
- Implement play/pause guards, status polling, and active-company display.

### M4 — Threads and polish

- Add Threads tab (thread DataTable + embedded snapshot viewer).
- SideRail hosts editable whiteboard on process pages.
- Add linked/unlinked filters, sub-agent/GPA picker, child-thread links.
- Visual regression baseline, accessibility pass, responsive drawer for side rail below 1280px.

## Dependencies

- [UI theme and design system](15-ui-theme-and-design-system.md) — required before feature UI work.
- API/OpenAPI contracts and generated types.
- Backend process/thread/whiteboard endpoints.
- Snapshot viewer requires agent checkpointing.

## Testing strategy

- Component tests for forms, tables, controls, dialogs, and accessibility.
- Zustand store tests for stale responses, pagination, and status transitions.
- Mock Service Worker contract fixtures generated from OpenAPI.
- Playwright E2E for manual vertical slice and process/thread navigation.
- Keyboard and screen-reader checks for row actions and dialogs.
- Visual regression tests for dense operational screens.

## Risks and open questions

- Final Records Viewer columns and filter presets need UX validation.
- Define whiteboard refresh cadence and whether historical effort selection is needed.
- Large thread snapshots need virtualization or server pagination.
- Blacklist badge from `SalesStrategyCompany.is_blacklisted` / `SalesStrategyProspect.is_blacklisted`.
- Unblacklist restores eligibility; mark-valid allowed when company is not blacklisted.
- Decide whether process logs are structured events or rendered text.

## Acceptance criteria

- All screens use the shared LOOP dark theme and semantic tokens (amber primary, dark surfaces, coral destructive).
- Operator completes the entire manual vertical slice in the UI.
- SalesStrategy opens on Strategy by default; tab bar matches approved active-tab styling.
- Records Viewer and Threads reuse the same DataTable pattern.
- Process pages show themed play/pause, metric tiles, logs, and whiteboard sub-tab.
- Theme toggle persists; side rail collapses gracefully on smaller viewports.
- Accessibility and E2E suites pass.
