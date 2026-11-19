# Environment

Real values for `dev-nicolas`. The agent reads this before touching anything.

## Boot

```
cd ~/odoo-doodba-template
docker compose -f devel.yaml up -d db
```

The Odoo service is not kept up for tests: each test runs in a one-off container over
the `db` service.

## Health

```
http://localhost:11069/web/login?db=scalpers
```

Only when the dev Odoo service is up. The module test below does not use this probe.

## Tests

`verify/config.env` runs two steps on a fresh, disposable database. The test module is
`scalpers_partner_vat_unique` (four post-install tests):

```
cd ~/odoo-doodba-template
DB="test_devkit_verify_$(date +%Y%m%d_%H%M%S)"
docker compose -f devel.yaml run --rm --entrypoint odoo odoo \
  --config=/opt/odoo/auto/odoo.conf -d "$DB" \
  -i scalpers_partner_vat_unique --stop-after-init --workers=0 --log-level=info
docker compose -f devel.yaml run --rm --entrypoint odoo odoo \
  --config=/opt/odoo/auto/odoo.conf -d "$DB" \
  -u scalpers_partner_vat_unique --test-enable --stop-after-init --workers=0 --log-level=test
```

`--entrypoint odoo` is deliberate: the doodba `40-addons-link` entrypoint fails with
`FileExistsError` when `/opt/odoo/auto/addons` already contains the links from a previous
container. The bypass uses the existing links and `/opt/odoo/auto/odoo.conf`.

Verified run: `20261118T102203-192659a`, `sha 192659a3c8d2`, `tests: pass`,
`test_vat_unique: Ran 4 tests ... OK`.

## Lint

```
bash guard/guard.sh
python3 guard/odoo_lint.py --root ../odoo-doodba-template
```

`guard/guard.sh` runs the kit's checks on the kit. `odoo_lint` skips `evals/`, so run it
with the Odoo tree as root to lint the modules there. The Odoo 11 quality base is at
`~/dev/odoo11-base`; apply it to a repo before relying on `pre-commit`.

## Database

- Engine: PostgreSQL 15 in `odoo-doodba-template-db-1`.
- Disposable database: `test_devkit_verify_<timestamp>` (created by the test command).
- Production: forbidden. The restored `scalpers` database is not used for tests.

## One-way doors

- Production deploy: human signature, company pipeline, never this host.
- Migrations: review the plan and the backup before running.
- Secrets: never in the repo, the config, the evidence or a prompt.
- Customer data: never copied into a fixture or an eval case.
