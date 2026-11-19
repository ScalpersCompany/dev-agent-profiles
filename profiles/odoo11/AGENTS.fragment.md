## Odoo 11 profile rules

- Target Odoo 11 only: v11 ORM, Python 2/3-compatible code, no OWL and no v12+ APIs.
- `sudo()` only in the paths listed in `guard/odoo_allowlist.txt`, with a test that proves the access rule.
- No `cr.commit()` in business code; the framework owns the transaction.
- No raw SQL without a written reason; parameterize it and add a test for the edge case.
- Every new or modified Odoo field has `help` (what it represents, unit/format and effect) and its documentation in the same commit.
- Views, security CSV, data XML and access rules load in a clean database before the change is done.
- Tests exercise the public behaviour of the module; a test that only mocks `run()` does not prove the rule.
- No comments in new or modified code; docstrings, `_description`, `help` and README are documentation.
- No production URL, credential or shared database; verify uses a disposable database.
- rsc-harness is optional. If the repo uses it, its skills live in `.rsc/skills` and are not copied into this profile.
