# The development base

This kit lives in the development base (`dev-nicolas`). It is not deployed to production.

## What it covers

- **Code repos**: the Odoo doodba tree and any other repo in the base. `verify/run.sh`, `guard/guard.sh` and `guard/odoo_lint.py` run there.
- **Skills**: Hermes and OpenCode `SKILL.md` files. The eval harness copies a skill into a disposable sandbox and scores it against a rubric.
- **EVA and Multica**: the evidence gate decides whether a ticket may move; the kit gives the agent the evidence and the guardrails it needs before asking for that move.

## The gate

A change reaches production only after:

1. `verify/run.sh` has run on the change and left evidence.
2. `guard/guard.sh` is green, or every skipped check has a written reason.
3. The applicable eval has passed its threshold.
4. The evidence gate has a `pass` row for the current commit.

The production deploy itself keeps a human signature. The kit never deploys.

## Isolation

Every verification and every eval runs in a disposable worktree or copy, with a disposable database when the test needs one. The live tree, the restored databases and the running containers are not touched.

## The order

Verification, guardrails, evals, autonomy. Automating the outer loop before the inner loop is green only produces faster noise.
