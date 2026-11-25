# GGA rules — hexagonal microservice profile

These rules are appended to the DevAgentKit core GGA rules. They add the contract for a
Scalpers microservice: pure domain, ports and adapters, contract-first, idempotency,
persistence, tests, Docker and evidence. The company rule and the core rules still apply.

The profile is domain-agnostic. A product, calling system or integration is an adapter or a
separate module; it never becomes a service folder or a shared transaction.

## BLOCKING — microservice

### Quality gates and evidence

- `uv sync --frozen` ran with the committed `uv.lock`; a diff that changes `pyproject.toml`
  without the lock change is `FAILED`.
- The project's configured linter and type checker ran on every changed `.py` file and
  passed. Do not lower the configured level, add a blanket ignore or delete a rule to make
  the change green.
- `pytest` ran the affected architecture, domain, use-case, contract, adapter, API, E2E and
  concurrency suites and passed. A test that is deselected, skipped or not collected is not
  evidence.
- `docker compose config` passed for the root compose and every changed Dockerfile has a
  successful build or a documented reason it cannot run locally. A health check that
  returns `200` without the service's dependencies is not enough.
- A gate that fails because a tool, Python version, container or network is missing is
  `ENV-FAIL`, not `PASS`; rerun in the pinned image.
- The pipeline evidence is the pipeline id and status for the head SHA of the merge
  request, with every required job in `success`. A green local run or a pipeline for an
  older SHA is not evidence.

### Domain and dependency rule

- An import in any `domain/` of a framework, HTTP client or server, SQL/ORM/engine,
  Pydantic, YAML, Docker, messaging or infrastructure module; `print()` or logging I/O in
  service code; a dependency from `domain/` to `application/`, `adapters/` or `api/`.
  `guard/hexagonal.sh` enforces the literal cases; the reviewer catches the dynamic ones.
- A business rule in a router, repository, controller, serializer or migration. The domain
  owns the rule; the use case orchestrates; the adapter translates.
- A service that reads another service's database, shares its transaction or reuses its
  internal model. Integrate through a contract or an adapter with its own lifecycle.
- A new product-specific word, table, endpoint or folder in the base profile. The profile is
  domain-agnostic; the integration lives in its adapter or its own repository.
- A `domain/` function with I/O, a clock that is not injected, randomness that is not
  injected or a global mutable singleton. Deterministic domain tests must be possible.

### Contract-first

- A JSON Schema 2020-12 or OpenAPI 3.1 change without the schema, the generated or checked
  client/type, an example and a contract test in the same change.
- A response or event field renamed, removed or retyped without a SemVer decision, a
  deprecation path and a consumer test.
- An error response that is not `application/problem+json` with a stable `type`/`code`, or a
  `502` that leaks the provider's message, stack trace or internal id. Log the provider
  detail; return a generic detail.
- A contract test that validates only the happy example and not the error codes, the
  required fields, the unknown-field policy or the nullability.

### Idempotency and provider calls

- A side effect or outbound call without an idempotency key `(consumer, request_id)`, a
  canonical body hash and a durable `pending` claim committed before the call.
- A retry after an unknown outcome (timeout after send, connection reset after send) that
  can duplicate a charge, an order, a shipment or a message. The rule is: rejection (4xx)
  is final; unavailable before send is `502` and may retry; unknown after send is `502` with
  no automatic retry and an explicit reconciliation path.
- A duplicate request that creates a second row, a second provider call or a second event.
  The duplicate must return the stored outcome or a conflict, never repeat the side effect.
- A concurrency test missing for a claim, a lock or a compare-and-set that protects a side
  effect. The test must run two workers or two requests against the same key.
- A provider secret, token or endpoint in code, a log, a fixture or a compose file. Read it
  from the environment and fail fast at startup when a required value is missing.

### Persistence and migrations

- A schema change without a migration, a rollback path and a test on a clean database.
- A new non-null column with a default or a backfill that can rewrite a large table without
  an engine-validated plan, a nullable intermediate column and an explicit backfill.
- A migration that assumes the provider, network or another service is available during
  deploy.
- A repository that hides a transaction boundary, commits inside a domain/use-case method
  or shares a transaction with an external system.
- A destructive `DELETE`/`UPDATE` without a bounded `WHERE`, a backup and explicit
  authorization.

### Tests

- A unit test that calls the provider network, a real shared database or a real queue.
  Adapters use cassettes or a local fake; domain and use cases use in-memory ports.
- A test that mocks the class under test, asserts only an internal call, or passes without
  the change.
- A contract, API, E2E or concurrency test missing for a new endpoint, event, side effect,
  idempotency key or error path.
- A test that passes locally only because a service, table or fixture exists in the local
  compose but not in the pipeline's clean environment.
- A success claim without the command, exit code, commit SHA and output or artifact path
  under `evidence/<run-id>/`.

### Security and operations

- A write endpoint without authentication, authorization and input validation, or a check
  that can be bypassed by a body field, a header or a path parameter.
- A secret in the diff, a log, a test fixture, a capture or a commit message.
- A container that runs as root, uses a mutable `latest` tag, mounts the Docker socket,
  publishes a database or uses host networking in the compose.
- A log line with a token, a full request body, a provider payload or personal data.
- A health or readiness endpoint that reports healthy before its required dependency is
  reachable, or a shutdown that drops an in-flight request without draining.

### Scope and hygiene

- Explanatory comments in new or modified code; docstrings and generated API documentation
  are documentation, not comments. Legal headers and tool directives are allowed.
- Dead or commented-out code, a `print()`, a debug dump, a temporary script, a `.bak`, a
  capture or a work file that reaches the diff.
- An unrelated refactor, a whole-file reformat, a dependency bump or another ticket mixed
  into the change.
- The same validation, error mapping or extraction written twice; it must be one helper
  reused by all adapters.
- A suppression (linter, type checker or test skip) without the exact code and a written
  reason.

## ADVISORY

- Naming, readability, duplication or a simpler structure that does not change behaviour.
- Broader coverage, a slower path outside the hot path, or a local performance improvement
  with no correctness risk.
- A framework or library idiom that is equivalent and already used by the service.
- A convenience endpoint, log field or diagnostic that helps operators.
