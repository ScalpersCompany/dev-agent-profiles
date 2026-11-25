# Changelog

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
