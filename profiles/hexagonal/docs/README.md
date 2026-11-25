# Profile documentation

The architecture, idempotency, persistence, testing and adaptation rules live in
`skills/scalpers-hexagonal-microservice/references/architecture.md`.

Profile-specific decisions:

- Python 3.12, FastAPI and Pydantic v2; `uv` for dependencies.
- One repo per pilot with `services/<name>/` and a root compose; split repositories only
  when the service leaves the pilot for the platform.
- The Odoo bridge is a separate module in `scalpers-v11`, with its own branch, pipeline and
  installation. It is not a folder of the microservice repository.
- The guard is the executable expression of the dependency rule; the skill explains why.
- Verify uses the target repository's own test command; never a shared or production database.
- Eval baseline is pending; add a case per new skill rule and record it in
  `docs/EVAL-BASELINE.md` when the neutral harness supports it.
