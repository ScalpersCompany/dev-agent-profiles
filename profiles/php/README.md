# PHP profile

The PHP profile uses the same gates as the Odoo profile:

- `guard`: PHPStan, PHPCS and PHPUnit on the staged files;
- `verify`: boot the dev server, hit the health endpoint and run the suite;
- `evals`: a case per skill or review rule that changes.

It needs no Odoo module, database or Python Odoo tree. The generic skills
(`dev-verify`, `repro-first`, `review-diff`, `correct`, `query-readonly`) are
shared; this profile only adds its domain skill.

The `profile.env` is the contract. The integration into `guard.sh` and
`install-hooks.sh` is the next migration phase; this directory is the target
shape, not a second runtime.
