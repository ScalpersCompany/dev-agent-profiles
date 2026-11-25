# Profile documentation

The architecture, idempotency, persistence, testing and adaptation rules live in
`skills/scalpers-hexagonal-microservice/references/architecture.md`.

Profile-specific decisions:

- Python 3.12, FastAPI and Pydantic v2 are the default stack; `uv` for dependencies. HTTP is a boundary choice, not an architecture requirement.
- One repo per pilot with `services/<name>/` and a root compose; split repositories only
  when the service leaves the pilot for the platform.
- The base is domain-agnostic: no product-specific rule. Integrations with
  existing systems are separate adapters or modules, with their own lifecycle; they are not
  service folders and do not share transactions with the microservice.
- The guard is the executable expression of the dependency rule; the skill explains why.
- Verify uses the target repository's own test command; never a shared or production database.
- Eval baseline is pending; add a case per new skill rule and record it in
  `docs/EVAL-BASELINE.md` when the neutral harness supports it.
