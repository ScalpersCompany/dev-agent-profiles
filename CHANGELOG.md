# Changelog

## [1.10.0] - 2026-11-27

### Cambiado

- `profiles/team` se convierte en `flows/team`: el flujo no es un perfil activable. Compone el
  perfil de lenguaje activo (o el declarado en `.dev-agent/team.env`) y se ejecuta con
  `dev-agent flow run team --spec <task-file>`.
- `flow.json` sustituye a `profile.json`; `entrypoint` sustituye a `runner`; `roles.json` usa
  `flow` en lugar de `profile`.
- `dev-agent flow list|run` descubre los flujos en `dev-agent-profiles/flows`; `dev-agent roles`
  sigue aceptando la ruta antigua de `profiles/team` para instalaciones existentes.
- El guard `guard/team.sh` se retira del flujo: el contrato se valida dentro del runner y el
  perfil base sigue aportando guard y verify. Las instalaciones antiguas conservan su copia.

### Added

- `flow.json` y `flow.schema.json` con nombre, versión, entrypoint, contrato, base y etapas.
- Tests del contrato de flujo y del comando `dev-agent flow` en el kit.

## [1.9.1] - 2026-11-26

### Cambiado

- `profiles/team` 0.1.2: el contrato y su README nombran el rol y no el producto, y el mapeo
  por agente se genera del mismo `roles.json` (`dev-agent roles <claude|opencode>`), sin
  presentar ningún agente como el de referencia.

## [1.9.0] - 2026-11-26

### Added

- `profiles/team`: role contract for work split across several agents on one repository. Four
  roles (`plan`, `dev`, `review`, `verify`) plus the kit's eval judge, each with its write
  surface, its closing command, and the rule that review and verify are read-only and run on a
  copy.
- `roles.json` and `roles.md`: the contract is machine-readable and validated by the profile
  guard, not only described.
- The profile delegates the language checks to the base profile declared in
  `.dev-agent/team.env`, so one active profile per repository still holds.
- CI runs the team profile contract and guard tests, the shell syntax check and the lint
  compilation.

### Fixed

- The task-file check accepts Markdown tables and scaffolding rows without a spec (`—`), and
  only requires an `S#` on `T<n>` task rows; a section now ends at any level-2 heading.

## [1.8.0] - 2026-11-25

### Added

- Complete E2E evidence in the Odoo 11, PHP 8 and hexagonal GGA rules: public entry point, real application, Playwright/API report, JUnit/JSON, traces and screenshots under `evidence/<run-id>/e2e/`.
- `E2E_CMD`, `E2E_BASE_URL` and `E2E_HEALTH_PATH` in the profile `verify/config.env.example` files.
- Profile READMEs state that `verify/run.sh` runs the E2E suite and keeps the artifacts.

### Changed

- A smoke probe is not complete E2E; a UI or user-flow change without the suite is blocking.

## [1.7.0] - 2026-11-25

### Added

- `profiles/odoo11/gga/REVIEW-RULES.md`: Odoo 11 / OCA blocking rules appended to the language-agnostic core: manifest and version, flake8, mandatory pylint, check-xml, pre-commit, pipeline evidence, OCA/ORM N+1, access rules, migrations, queue and real MR failure patterns.
- `profiles/php/gga/REVIEW-RULES.md`: PHP 8 rules for strict types, PSR-12, PHPStan, PHPCS, PHPUnit, Composer and application security.
- `profiles/hexagonal/gga/REVIEW-RULES.md`: microservice rules for domain purity, contract-first, idempotency, provider outcomes, problem+json, persistence, tests, Docker and evidence.

### Changed

- GGA rules are profile-owned; one profile's language rules never apply to another. The core keeps only the language-agnostic contract.

## [1.6.0] - 2026-11-25

### Changed

- Made the `hexagonal` profile domain-agnostic: removed product- and system-specific rules from
  the AGENTS fragment, README, docs, checklist and skill.
- The skill now describes integrations with existing systems as separate adapters or modules,
  without naming a concrete system or its tables.
- Generic service tree and compose examples.

## [1.5.0] - 2026-11-25

### Added

- `profiles/hexagonal`: profile for Scalpers microservices with the domain guard, verify
  example, profile rules and the `scalpers-hexagonal-microservice` skill.
- Guard against framework, HTTP, SQL, YAML and infrastructure imports in `domain/`, and
  against `print()` in service code; unit tests for the guard.
- Root README entry and profile documentation.

## [1.4.0] - 2026-11-19

### Changed

- Related repositories no longer name a fixed product repository; the target is the repository where development happens, whatever the stack, with the kit and the active profile at its root.

## [1.3.0] - 2026-11-19

### Added

- Related-repositories table with the core, this profiles repo, `scalpers-tech-doc` and the product repo; the company norm is referenced, never copied.

## [1.2.0] - 2026-11-19

### Changed

- Removed the knowledge-layer references from the Odoo plan and the skill coverage; `engram` remains a local core layer, not a profile concern.

## [1.1.0] - 2026-11-19

### Changed

- Published as `ScalpersCompany/dev-agent-profiles` (public); the README and the Odoo profile point to the company repository and the company norm.

## [1.0.0] - 2026-11-19

### Added

- Initial profiles repository: `profiles/odoo11` extracted from `dev-agent-kit` and the `profiles/php` skeleton.
- Odoo 11 guard, allowlist, verify example, skills, eval cases, rubrics, tests and docs.
- Profile contract and root README.
