# Changelog

## [1.1.0] - 2026-11-25

### Added

- `gga/REVIEW-RULES.md`: Odoo 11 / OCA blocking rules, appended to the language-agnostic core by `install-gga.sh --profile`.
- GGA coverage for manifest/version/changelog, flake8, mandatory pylint, check-xml, pre-commit, pipeline evidence, OCA/ORM N+1, access rules, migrations, queue and real MR failure patterns.

## [1.0.0] - 2026-11-19

### Added

- Odoo 11 profile extracted from `dev-agent-kit`: linter, allowlist, verify example, Odoo skills, eval cases, rubrics, tests and Odoo documentation.
- `profile.json` and `profile.env` contract, `AGENTS.fragment.md` and `guard/odoo.sh`.

### Changed

- The core kit no longer contains Odoo checks; `guard.sh` loads the active profile.
