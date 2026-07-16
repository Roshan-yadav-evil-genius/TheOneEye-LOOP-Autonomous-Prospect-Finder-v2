# Foundation and Monorepo Plan

## Objectives and scope

Create the production `loop/` monorepo, shared engineering conventions, local developer environment, and minimum deployable API/web/runtime shells. This plan establishes boundaries and tooling; it does not implement business workflows.

## Functional requirements

- Provide runnable shells for `api`, `web`, `worker`, `scheduler`, `agent-runtime`, `browser-pool`, `admin`, and `cli`.
- Expose health, readiness, and version endpoints.
- Provide typed environment configuration and development seed commands.
- Generate frontend TypeScript types from OpenAPI.
- Support one-command local dependency startup and deterministic test setup.

## Non-functional requirements

- Clean checkout to working development environment in under 30 minutes.
- Reproducible builds with pinned lockfiles.
- Strict Python and TypeScript checks in CI.
- No package under `packages/` may import from `apps/`.
- Secrets never committed; safe defaults fail closed outside development.

## Architecture and design decisions

- Python workspace for FastAPI/domain packages; Node workspace for React/admin/browser packages.
- Modular monolith first, with bounded contexts under `apps/api`.
- Twelve-factor configuration through a typed `Settings` object.
- OpenAPI is the cross-language contract source of truth.
- Trunk-based development and short-lived branches.
- ADRs are required for significant deviations from the canonical design.

## Data models

No business entities are owned here. Foundation defines:

- `BuildInfo`: version, commit SHA, build timestamp.
- `HealthStatus`: service name, status, dependency checks.
- Configuration schemas for PostgreSQL, Redis, object storage, telemetry, and model providers.

## APIs and interfaces

- `GET /health/live`
- `GET /health/ready`
- `GET /version`
- `Settings.load()`
- Shared error envelope: `code`, `message`, `details`, `request_id`.
- CI interfaces: lint, typecheck, unit, integration, contract, build.

## Target directory structure

```text
loop/
├── apps/
│   ├── api/
│   ├── web/
│   ├── worker/
│   ├── scheduler/
│   ├── agent-runtime/
│   ├── browser-pool/
│   ├── admin/
│   └── cli/
├── packages/
│   ├── config/
│   ├── contracts/
│   ├── logging/
│   ├── telemetry/
│   ├── validation/
│   ├── shared-types/
│   └── testing/
├── infrastructure/
├── deployment/
├── scripts/
├── tests/
└── docs/architecture/adr/
```

## Milestones and implementation tasks

### M1 — Workspace bootstrap

- Create Python and Node workspaces with lockfiles.
- Add formatting, linting, typechecking, test, and build scripts.
- Define import-boundary checks and naming rules.
- Add contribution, environment, and ADR templates.

### M2 — Runtime shells

- Create minimal FastAPI app and React/Vite shell with LOOP dark theme tokens, ThemeProvider, and PageShell ([UI theme plan](15-ui-theme-and-design-system.md)).
- Create process entry points for remaining runtime apps.
- Add health/version endpoints and graceful shutdown hooks.
- Add shared typed configuration.

### M3 — Local development

- Provide local PostgreSQL, Redis, and object-storage profiles.
- Add `.env.example` without secrets.
- Add bootstrap, seed, reset, and generated-types commands.
- Document debugging and test workflows.

### M4 — CI baseline

- Run Python/TypeScript quality gates, tests, OpenAPI generation, and container builds.
- Add dependency/security scanning and secret detection.
- Cache dependencies without hiding lockfile drift.

## Dependencies

- None.
- Enables every other component.
- Infrastructure and Testing plans begin in parallel with this plan.

## Testing strategy

- Smoke-test every runtime entry point.
- Test configuration validation for missing/invalid values.
- Verify health semantics with unavailable dependencies.
- Verify generated OpenAPI and TypeScript output is deterministic.
- Test a clean environment bootstrap in CI.

## Risks and open questions

- Final package managers and workspace tooling need an ADR.
- Avoid creating all service infrastructure before its runtime is needed.
- Decide whether browser/admin Node packages share the frontend workspace.
- Decide where generated clients are committed versus generated during CI.

## Acceptance criteria

- A clean checkout builds and tests without undocumented manual steps.
- API and web shells run against local dependencies.
- CI blocks lint, typing, test, contract, secret, and build failures.
- Package dependency-direction checks pass.
- All runtime images expose health/version metadata.
