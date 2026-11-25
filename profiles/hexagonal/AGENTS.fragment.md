# Microservice profile rules

- The company norm is `ScalpersCompany/scalpers-tech-doc/AGENTS.md`; this fragment only adds microservice rules. If they conflict, the company norm wins.
- Python 3.12 + FastAPI + Pydantic v2; `uv` for environments and lock files.
- `domain/` imports only the standard library and domain modules. No FastAPI, Pydantic, SQL, HTTP, YAML or infrastructure; `guard/hexagonal.sh` enforces it.
- The contract is the source of truth: JSON Schema 2020-12 and OpenAPI 3.1, SemVer, examples and contract tests in the same change.
- Business rules live in the domain; use cases orchestrate; adapters translate. Routers and repositories do not decide policy.
- Idempotency is `(consumer, request_id)` with a canonical body hash and a durable `pending` claim before any provider call.
- Distinguish provider rejection (4xx), provider unavailable before send (502) and unknown outcome after send (502, no automatic retry).
- Errors use `application/problem+json` with stable codes. A 502 never leaks the provider message; log it and return a generic detail.
- Secrets only from the environment; fail fast at startup when a required variable is missing.
- Never add column defaults to fields on huge tables (`stock.picking`, `account.move`, ...); add nullable columns and write explicitly.
- Pilot layout: one repo with microservices in `services/<name>/`, one root `compose.yaml` and a Dockerfile target per service. Platform repos split later per the methodology.
- The Odoo bridge is a separate Odoo module in `scalpers-v11`; it is not a service folder and does not share transactions with the service.
- Tests: architecture, domain, use cases, contract, adapters with cassettes, API, E2E and concurrency. No provider network in unit tests.
- Every service ships README, `CHANGELOG.md` and observed evidence; no claim without command output.
- Production is untouched without explicit authorization for that action.
