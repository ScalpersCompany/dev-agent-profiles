---
name: odoo-safe-change
description: "Edit Odoo modules without breaking access rules or transactions."
version: 1.1.0
author: Nicolas Ramos
---

# Safe Odoo change

Use when editing Python, XML, CSV or PO files of an Odoo module.

Kit root: `KIT="${DEV_AGENT_KIT:-$HOME/dev-agent-kit}"`. If the current repo has no
`guard/` or `evidence/`, use the same paths under `$KIT`.

## Preflight

- Read `__manifest__.py`, `security/`, `data/`, `views/` and `tests/`.
- Locate the model and every existing caller with `grep`.
- Find the existing tests for that model. If there are none, write one first.

## Rules

- ORM first. No raw SQL. If SQL is unavoidable, parameterize it and add a test for the edge case.
- No `sudo()` unless the file is in `guard/odoo_allowlist.txt` (or
  `$KIT/guard/odoo_allowlist.txt` when the repo has no kit). If it is needed, justify it
  in the PR and test the access rule.
- No `cr.commit()`. The framework owns the transaction.
- Reuse XML IDs. Do not create a second record for an existing concept.
- Translations go in `.po` files, not hardcoded Spanish in Python.
- Schema or data migrations go under `migrations/<version>/` and are tested on a disposable database.
- A new stored field needs a view, an upgrade path and, when queried often, an index.

## Verification

1. Install or upgrade the module on a disposable database.
2. Run the module tests with `--test-tags`.
3. Load the views and the menu as a user with the real groups, not as admin.
4. Save the commands and the outputs in `evidence/` (repo or `$KIT/evidence/`).
