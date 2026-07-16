# Infrastructure and Deployment Plan

## Objectives and scope

Provision local, development, staging, and production environments; package and deploy all runtime applications; manage PostgreSQL/Redis/object storage, browser-capable nodes, networking, secrets, observability, backups, promotion, rollback, and scaling.

## Functional requirements

- Build versioned images for API, web, worker, scheduler, agent-runtime, browser-pool, admin, and CLI.
- Provision PostgreSQL, Redis, object storage, ingress/TLS, telemetry, and encrypted browser profile storage.
- Run migrations as controlled release jobs.
- Deploy automatically to development/staging and promote explicitly to production.
- Support feature flags, rollback, backup/PITR, restore, and disaster-recovery drills.
- Isolate browser nodes and restrict network/secrets access.

## Non-functional requirements

- Cloud-agnostic core and infrastructure-as-code.
- Reproducible immutable images with SBOM/signature/scanning.
- API 99.5% business-hours target; RPO 15 minutes, API RTO 60 minutes.
- Zero-downtime compatible API/database releases.
- Environment parity with different scale/cost, not different architecture.

## Operational security

LOOP has **no application authentication** (single trusted operator). Operational security still applies:

| Concern | Requirement |
|---------|-------------|
| Secrets | Vault or K8s secrets — never in repo |
| Encryption | TLS in transit; encrypted DB volumes and object storage at rest |
| Network | Deploy API/web on trusted network or VPN |
| PII | Minimize LinkedIn data; retention and export policies documented |
| Audit | Append-only audit log for registrations, blacklists, funnel transitions |
| Browser | Operator maintains logged-in LinkedIn session on browser host; agents use MCP only |

## Architecture and design decisions

- Docker per runtime; Kubernetes/Helm target for production.
- Terraform for cloud resources; Helm/Kustomize decision recorded in ADR.
- Managed PostgreSQL/Redis preferred in production.
- Separate node pool/security profile for browser workloads.
- Expand-first migrations run before application rollout; contract cleanup in later release.
- Git-based CI/CD with staging auto-deploy and production approval.

## Data models

No business entities. Operational definitions:

- Environment configuration and secret references.
- Deployment release metadata.
- Feature-flag values.
- Backup/restore records.
- Capacity/SLO budgets per runtime.

## APIs and interfaces

- Container health/readiness endpoints.
- IaC modules for network, database, cache, storage, compute, observability.
- Deployment values per environment.
- CI jobs: build, scan, sign, migrate, deploy, verify, promote, rollback.
- Runbook interfaces for scale, restore, rotate, drain, and recover browser profile.

## Target directory structure

```text
loop/infrastructure/
├── terraform/
│   ├── modules/
│   └── environments/
loop/deployment/
├── helm/
├── environments/
└── policies/
loop/.github/workflows/  # or equivalent CI
loop/docs/runbooks/
```

## Milestones and implementation tasks

### M1 — Local and development

- Add container builds, local dependency profiles, Terraform development environment, registry, TLS ingress, and baseline telemetry.

### M2 — Staging pipeline

- Add staging cluster/services, migration job, seeded smoke environment, image scanning/signing, automated deploy and E2E.

### M3 — Production platform

- Add HA managed data services, encrypted backups/PITR, browser node pool/profile provisioning, autoscaling, disruption budgets, and production secrets.

### M4 — Safe delivery and recovery

- Add canary/rolling rollout, feature flags, rollback automation, restore drills, capacity tests, cost controls, and disaster runbooks.

## Dependencies

- Foundation runtime entry points and health contracts.
- Database backup/migration requirements.
- Observability collectors/dashboards.
- Security secrets/network/encryption controls.
- Browser runtime has specialized node/profile needs.

## Testing strategy

- IaC validation/plan in CI and policy-as-code checks.
- Container smoke, vulnerability, SBOM, and signature verification.
- Staging migration/rollback compatibility tests.
- Pod/node/process failure and autoscaling exercises.
- Database PITR and object restore drills.
- Browser node replacement/session recovery tests.
- Full deployment synthetic checks after each rollout.

## Risks and open questions

- Select cloud provider and managed-service offerings.
- Kubernetes may be excessive for earliest internal deployment; document a smaller initial target while preserving container boundaries.
- LinkedIn Chrome profile provisioning is stateful and needs explicit operational ownership.
- Define production region, residency, and egress restrictions.
- Establish cost budgets before scaling agent/browser capacity.

## Acceptance criteria

- A tagged release builds once and promotes unchanged through environments.
- Development/staging deployments are automated and production rollback is documented/tested.
- Migration failures halt rollout safely.
- Backup restore meets RPO/RTO in a drill.
- Browser workloads are isolated and encrypted.
- Images pass scan/signature policy and all services expose reliable readiness/liveness.
