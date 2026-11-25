# Microservice profile rules

- The company norm is `ScalpersCompany/scalpers-tech-doc/AGENTS.md`; this fragment only adds microservice rules. If they conflict, the company norm wins.
- Python 3.12 + Pydantic v2; `uv` for environments and lock files. FastAPI is the default HTTP boundary, not an architecture requirement.
- `domain/` imports only the standard library without I/O or concurrency (see the profile README for the denied modules) and domain modules. No FastAPI, Pydantic, SQL, HTTP, YAML or infrastructure; `guard/hexagonal.sh` enforces it.
- The contract is the source of truth: JSON Schema 2020-12 and OpenAPI 3.1, SemVer, examples and contract tests in the same change.
- Business rules live in the domain; use cases orchestrate; adapters translate. Routers and repositories do not decide policy.
- When the service has side effects or outbound calls, idempotency is `(consumer, request_id)` with a canonical body hash and a durable `pending` claim before the call.
- When the service calls a provider, distinguish rejection (4xx), unavailable before send (502) and unknown outcome after send (502, no automatic retry).
- Errors use `application/problem+json` with stable codes. A 502 never leaks the provider message; log it and return a generic detail.
- Secrets only from the environment; fail fast at startup when a required variable is missing.
- A default or backfill on a new column can rewrite a large table; validate it with the engine and use nullable columns plus an explicit backfill.
- Pilot layout: one repo with microservices in `services/<name>/`, one root `compose.yaml` and a Dockerfile target per service. Platform repos split later per the methodology.
- The base is domain-agnostic: no product-specific rule. Integrations with existing systems are separate adapters or modules, never service folders, and never share a database transaction with the service.
- Tests: architecture, domain, use cases, contract, adapters with cassettes, API, E2E and concurrency. No provider network in unit tests.
- Every service ships README, `CHANGELOG.md` and observed evidence; no claim without command output.
