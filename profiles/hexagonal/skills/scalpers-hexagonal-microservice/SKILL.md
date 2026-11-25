---
name: scalpers-hexagonal-microservice
description: "Trigger: microservicio nuevo, arquitectura hexagonal, puertos y adaptadores, FastAPI, contrato, idempotencia. Blueprint Scalpers para servicios testeables."
license: Apache-2.0
metadata:
  author: "nramosscalpers"
  version: "1.0"
---

## Activation Contract

Load before designing, creating, restructuring or reviewing a Scalpers microservice in any domain (transport, billing, catalog, notifications, warehouse). First read the company entry rule in `~/.agents/AGENTS.md` and the project-bound methodology; this skill implements the service slice of that methodology.

## Hard Rules

- `domain/` imports only the standard library and domain modules: no FastAPI, Pydantic, HTTP, SQL, YAML or infrastructure.
- The contract is the source of truth: validate request and response against its JSON Schema/OpenAPI, version it with SemVer and cover it with contract tests.
- Business rules live in the domain; use cases orchestrate; adapters translate. An adapter never decides business policy.
- Idempotency is `(consumer, request_id)` plus a canonical body hash and a durable `pending` claim before any provider call.
- Distinguish provider rejection (4xx), provider unavailable (before send) and unknown outcome (after send). Never auto-retry an unknown outcome.
- Secrets only from the environment. Fail fast at startup when a required variable is missing.
- Never add column defaults to fields on huge tables (`stock.picking`, `account.move`, ...): Odoo backfills every row on install. Add nullable columns and write explicitly.
- Every service ships tests, `CHANGELOG.md`, README and observed evidence. No claim without command output.
- Pilot: one repo with services in subfolders and one root compose. Platform: split repos per the Scalpers methodology. The Odoo bridge is a separate module, never a service folder.
- The company methodology prevails: product artifacts, roles and DoR/DoD live in the methodology; this skill only covers the service implementation slice.
- Scalpers rules: production untouched without explicit authorization; conventional signed commits without AI attribution; Spanish documentation, English code.

## Decision Gates

| Question | Choose |
|---|---|
| New bounded context or new use case? | New service only if it owns data and lifecycle; otherwise add a use case and port to the existing service. |
| Pilot or platform layout? | Pilot: one repo, `services/<name>/`, root compose. Platform: split `_doc`, `_test`, `_infra` and component repos later. |
| Sync or async? | Sync HTTP for request/response; queue or events only for long or decoupled work. |
| SQLite or PostgreSQL? | SQLite for local tests; PostgreSQL for shared or deployed services. |
| New adapter or new port? | New port only for a new domain capability; otherwise implement the existing port. |
| Contract change? | Additive = minor; remove, rename or tighten = major with migration window. |

## Execution Steps

1. Write the bounded context, use cases and contract change before code.
2. Implement the pure domain: entities, value objects, statuses, errors.
3. Declare ports in `domain/ports.py`; never leak adapter types.
4. Build DTO validation and domain mapping; keep contract field names.
5. Implement use cases with idempotency, error mapping and transaction boundaries.
6. Implement adapters behind ports; test them with cassettes or fakes, never live provider calls.
7. Expose HTTP with `problem+json`, auth and OpenAPI from an explicit composition root.
8. Add SQL migrations, YAML config with `${VAR}` resolution and fail-fast startup.
9. Add architecture, unit, contract, API and E2E tests; run them and capture evidence.
10. Add Dockerfile/compose, observability and README/CHANGELOG; commit one reviewable unit.

## Output Contract

Return the service tree, the contract and its version, the tests and commands with observed results, the `CHANGELOG.md` entry, the risk line and any pending decision. For a review, list findings by severity with `file:line` and evidence.

## References

- `references/architecture.md` — layer rules, contract, idempotency, persistence, testing, deployment and adaptation to other domains.
- `references/metodologia-scalpers.md` — how the company methodology maps to a microservice and what stays outside.
- `references/checklist.md` — delivery and review checklist.
- `assets/service-tree.md` — target tree, root compose and Dockerfile sketch.
