# Changelog

## [1.0.0] - 2026-11-19

### Added

- Odoo 11 profile extracted from `dev-agent-kit`: linter, allowlist, verify example, Odoo skills, eval cases, rubrics, tests and Odoo documentation.
- `profile.json` and `profile.env` contract, `AGENTS.fragment.md` and `guard/odoo.sh`.

### Changed

- The core kit no longer contains Odoo checks; `guard.sh` loads the active profile.
