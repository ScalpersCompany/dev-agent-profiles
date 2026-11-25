# GGA rules — Odoo 11 profile

These rules are appended to the DevAgentKit core GGA rules. They add the Odoo 11 / OCA
contract: manifest and version, lint and pipeline, ORM performance, access rules, XML,
migrations and the failure patterns observed in real merge requests of the product
repository. The company rule and the core rules still apply.

## BLOCKING — Odoo 11

### Manifest, version and changelog

- A functional change is any added, modified or deleted file of a module outside `tests/`,
  `README.rst`, `CHANGELOG.md` and `static/description/`. It includes `depends`, `data`,
  `external_dependencies`, `i18n/` and `migrations/`.
- A commit with a functional change in module `M` must change `version` in
  `M/__manifest__.py` in the same commit. The diff must show old and new `version` lines,
  both in `11.0.X.Y.Z`, and the new one strictly greater component by component.
- A functional file in the diff without a `version` hunk is `FAILED` at the first
  functional line.
- The same commit must add a `M/CHANGELOG.md` entry headed by the new version and update
  `M/README.rst`.
- A new module starts at `11.0.1.0.0`; manifest, README and CHANGELOG are in the same
  commit as its first functional code.
- A commit that only touches `M/tests/` must not change `version` and must not add a
  CHANGELOG entry.
- A `M/migrations/<v>/` directory must match the new manifest version.
- The version cannot be compared with the merge-base from the staged diff alone; require
  the evidence described in **Quality gates and evidence**.

### Quality gates and evidence

- A gate is `PASS` only with this evidence for the head commit: command, exit code `0`,
  commit SHA and the output or artifact path under `evidence/<run-id>/`. Any other state
  (`ENV-FAIL`, `NOT RUN`, `SKIPPED`, `FAIL`) is not a pass and must be reported as such.
- A gate that fails for an environment reason (import error, tool or Python version
  mismatch, missing network) is `ENV-FAIL`, not `PASS`. It needs a rerun in the pinned
  runtime, or it stays pending. The words “green” or “OK” next to an `ENV-FAIL` gate are a
  blocking finding.
- `flake8`: both hooks (`flake8 except __init__.py` and `flake8 only __init__.py`) ran on
  every changed `.py` file and passed.
- `pylint`: the hook `pylint with mandatory checks` (`.pylintrc-mandatory`, `pylint-odoo`)
  ran on every changed `.py` file and passed; `pylint-odoo` manifest checks run through
  `__manifest__.py`. `manifest-required-author` is ignored by design in own modules; no
  other mandatory check may be ignored. The optional `--exit-zero` hook is never evidence.
- `check-xml`: passed on every changed XML file.
- `pre-commit`: the run lists every hook with its result. `SKIP=`, `--no-verify` and edits
  to `.pre-commit-config.yaml`, `.flake8`, `.pylintrc*` or `.gitlab-ci.yml` made inside the
  change are blocking unless that file is the stated subject of the change.
- Pipeline: the evidence is the pipeline id and status for the head SHA of the merge
  request, with the `test` job in `success`. A pipeline for an older SHA, `skipped`,
  `canceled`, `manual`, one excluded by the job rules, or a green local run is not
  evidence. `sonarqube-check` is `allow_failure` and never counts as a gate.
- A job that is green only because tests were skipped, deselected or not imported is not
  `PASS`.
- A claim that the branch is current requires
  `git rev-list --count HEAD..origin/<target>` in the evidence. A positive count on a
  branch that touches the same modules requires a rebase before any gate is accepted.
- Version against base: for each changed module, include the manifest version at
  `git merge-base HEAD origin/<target>` and at the head, and the version at the target
  tip, proving head > base and no collision with the target tip.

### Odoo 11 correctness and OCA style

- A feature not available in Odoo 11 or the supported Python runtime: `with_user`,
  `with_company`, `@api.model_create_multi`, `create()` with a list of dicts,
  `filtered_domain`, `env.company`, `env.companies`, `env.su`, `flush()`, OWL, `Command`.
  Use `sudo(user)`, one dict per `create`, and `invalidate_cache`.
- `@api.one` is available but deprecated in v11; it is a finding of the mandatory
  `pylint-odoo` gate. Do not use it in new code. This rule does not replace that gate.
- `type="json"` is valid in v11 and is not a finding by itself. The finding is a route that
  bypasses access rules or validation.
- `super(Class, self)` is the normal OCA 11 style; it is not a finding.
- `f-strings` and syntax newer than the pinned Python runtime are a finding only when that
  runtime is below 3.6; verify the runtime before reporting.
- `ensure_one()` missing on a method that assumes one record; missing `for record in
  self` in a multi-record constrain.
- `float` money or quantity compared without `float_compare`; `datetime.now()` where a
  stored or compared `Datetime` field requires `fields.Datetime.now()`. `datetime.now()`
  for a log line or elapsed measurement is not a finding.
- `product_uom_qty` summed or rounded with the product UoM rounding; use `product_qty` or
  `uom._compute_quantity` explicitly.
- A new or modified field without `help` when the field is new or its semantics changed.
  A cosmetic change to `string` does not require a new `help`; a documentation-only
  omission is not blocking unless the field's meaning is now unclear.
- `_description` missing on a new model; `README.rst` missing; recordset names that end in
  `_id` (OCA style uses `partner`, not `partner_id`); duplicated extraction of the same
  business expression.

### OCA / ORM performance and correctness

- `search`, `search_count`, `search_read`, `read_group`, `browse(<single id>)`, `read`,
  raw `cr.execute`, `invalidate_cache` or `create`/`write`/`unlink` of a related lookup
  inside a `for`, a comprehension, a lambda passed to `mapped`/`filtered`/`sorted`, an
  `@api.depends` compute, a cron, a wizard line builder or an onchange when the iterated
  collection grows with business data.
  Fix: one `search`/`search_read`/`read_group` before the loop with `('id', 'in', ids)` or
  a relation domain, resolved to a dict, or `browse(ids)` once.
  Exception: the iterated collection is a literal or a fixed configuration list of at most
  10 items, or the lookup must observe a write made in the same transaction and a test
  proves it. A per-record `create` with different values is allowed in Odoo 11.
- `len(recordset)`, `len(self.search(...))` or the truthiness of a full `search()` used to
  decide existence or to count. Fix: `search(domain, limit=1)` for existence,
  `search_count(domain)` for counts. `len()` on a recordset already loaded for another
  reason is allowed.
- `search(domain)` without `limit` on a model whose size grows with business data
  (products, partners, sale or purchase orders, stock moves and pickings, account moves
  and lines, attachments, messages) in business code, unless the domain is constrained by
  ids or by a relation of the current records. `search([])` on such a model is always
  `FAILED`. Migrations and one-off scripts are exempt.
- Counting, summing or grouping in Python records that a `read_group` using the field's
  `group_operator` could aggregate: `sum(r.f for r in self.search(d))`,
  `len([r for r in self.search(d) if ...])`, or dicts built by looping a `search`.
  Allowed when the records are already loaded and needed for another reason in the same
  method.
- Per-record `write()` with identical values or per-record `unlink()` in a loop. Fix:
  `records.write(vals)` / `records.unlink()` once. Loops with different values per record
  are allowed. In Odoo 11 `create` takes one dict: do not request batch create; hoist the
  lookups instead.
- `browse(rec.id)`, `self.env[model].browse(x.id)` or `invalidate_cache()` inside a loop
  that breaks prefetch. Use the recordset directly or `mapped` / `filtered`.
- A lookup that decides between creating and reactivating, or that detects duplicates, on
  a model with an `active` field without `with_context(active_test=False)` (archived
  record ignored, duplicate created). Reading `one2many` caches after a write in the same
  transaction to decide that is also a finding; use an explicit `search`.
- `read_group` with `orderby` (not `order`), the field's `group_operator`, or a
  `groupby` on a non-stored field. Reimplementing `read_group` by hand in Python is a
  finding.
- Aggregating quantities of moves or lines with `product_uom_qty` across different UoMs.
  Use `product_qty` (product UoM) or `uom._compute_quantity` explicitly.
- SQL with interpolation, `cr.commit()` in business code, or `sudo()` outside the profile
  allowlist; missing ACL or `ir.rule` for a new model or a new access path.

### Security and data access

- Missing `ir.model.access.csv` for a new model, including a `TransientModel`; missing
  `ir.rule` for a record rule the domain does not protect.
- `sudo()` outside the profile allowlist, especially in a controller; an admin token or
  elevated permission used to work around access rules.
- A credential, token, password, hash or derived credential field readable by a
  non-administrator group. Cite the ACL row that grants the read.
- Raw SQL without parameters, a written justification and an edge-case test;
  `cr.commit()` in business code; an unparameterised write that can corrupt data.
- A new or modified route with `auth="user"` or `auth="public"` that creates or modifies
  payments, refunds, orders, stock or accounting without an explicit group check and a
  check that the record's company (journal, warehouse, order) belongs to
  `env.user.company_ids`. It needs a test with a user without the group and a user of
  another company.
- A route or token handler that accepts a model name, group, field or dotted path from the
  request without checking it against an allowlist. A token restricted to `sale.order`
  must not reach `partner_id.email` or any other model through a dotted path.

### Migrations, XML and data

- Renaming or deleting a persisted field or model without a migration; a migration that
  would not run on a new install (`post_init_hook` where needed).
- A destructive `UPDATE`/`DELETE` without a bounded `WHERE`, a backup, a dry run or a log;
  an `UPDATE` without `WHERE` is always blocking.
- A migration folder whose version is not the new manifest version.
- An incomplete `depends`: a module used directly (xmlid in `env.ref`, `ref=`, `groups=`,
  `inherit_id`, `_inherit`, a `comodel_name`, a decorator or a class import) and absent
  from the manifest. A transitive closure is not a reason to omit a direct dependency.
- An unused dependency, or a dependency used only by `tests/`; test-only dependencies must
  not install in production.
- A view, XML id, security CSV, data file or asset that does not load in a clean database;
  a core view edited directly; a duplicated XML id; a missing `noupdate="1"` on
  customer-editable data.
- A `migrations/<v>/` script that uses relative imports across a non-package, assumes a
  column exists on a new install, or runs `env.cr.commit()`.

### Queue, jobs and terminal states

- `RetryableJobError` used for a terminal state; an all-cancelled product or a permanent
  business condition that will retry forever.
- A job that retries a condition that cannot change, or swallows an exception and leaves
  the record in a half-finished state.

### Odoo tests and evidence

- A test disabled, commented out, deleted, not imported or marked skip only to make the
  pipeline green.
- A test tied to the internal `run()` of a connector, or a `SimpleNamespace` that never
  goes through the real `write()`; a test that passes without the change, or only fails by
  floating-point noise.
- A stock or procurement test that creates products or orders relying on defaults from
  other installed modules (`route_ids`, company, `date_planned`, `priority`, demo
  records). Set every value the closure's overrides read explicitly. A local green
  without the pipeline green for the same commit is not evidence.
- A test that is green only because the local database has demo data, the module closure
  is incomplete or `--test-enable` was not used.
- A website, portal, SGA or back-office flow changed without a browser E2E spec that logs
  in with a test user, reaches the page through the public route and asserts the visible or
  persisted result. Use Playwright or an Odoo tour only if the profile installs it; the
  evidence is the command, `0`, SHA, HTML/JSON report and trace or screenshot under
  `evidence/<run-id>/e2e/`.
- An E2E that runs against production, a shared database or a fixture that another team
  can change during the test.

### Known failure patterns from real MRs

- A `depends` that repeats the closure, or an unused/test-only dependency that installs
  production modules; a missing direct dependency that only fails when the module is
  installed alone (`External ID not found`).
- A test tied to the internal `run()` of a connector, or a `SimpleNamespace` that never
  goes through the real `write()`; a test that passes without the change, or only fails by
  floating-point noise.
- A local green E2E that fails in CI because the full closure changes `route_ids`,
  `company_id`, `date_planned`, `priority` or demo data.
- A new endpoint with `auth="user"` accepting payments or refunds without group and
  company checks; a `READ ONLY` transaction that is bypassed by `env.cr.commit()`.
- Three different regexes extracting the same business code; a sanitisation dependency
  that is unnecessary because the source is already ASCII.
- A branch many commits behind the target; a prose comment, a dead test or an unrelated
  refactor reaching the diff.
- Pylint hooks failing on a stale isort under Python 3.10 are `ENV-FAIL`, not `PASS`.
