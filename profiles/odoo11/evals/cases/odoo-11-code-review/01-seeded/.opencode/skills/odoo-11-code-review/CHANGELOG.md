# Changelog

## [1.2.1] - 2026-11-18

### Changed

- Removed the reviewer CLI and model names from `Segunda opinión`: the command
  uses `<reviewer-cli>` and `<approved-model>` placeholders, and the canonical
  model id stays in the internal register.

## [1.2.0] - 2026-11-18

### Added

- `Contrato del parte`: `fichero:línea` even for absent files (cite the manifest
  line), one line per field without `help=`, no "SQL injection" for an integer
  interpolation, and only v11 APIs.
- `models.Constraint` is v12+; v11 uses `_sql_constraints`.
- `@api.one` with a `search` inside counts as N+1.

## [1.1.0] - 2026-11-17

### Added

- Initial checklist: v11 compatibility, model, views, security, performance,
  data, tests and documentation.
