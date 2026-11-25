# Odoo 11 profile

This profile carries the Odoo 11 guard, verify example, domain skills and eval
cases. The core `dev-agent-kit` provides the gate, the hooks and the generic
skills; this directory only adds what is Odoo-specific.

## Contents

```text
profile.json                 contract
profile.env                  runtime values
AGENTS.fragment.md           Odoo rules added to the repo AGENTS.md
gga/REVIEW-RULES.md          Odoo 11 blocking rules appended to the core GGA rules
guard/odoo.sh                profile guard entry point
guard/odoo_lint.py           sudo, cr.commit, raw SQL, print checks
guard/odoo_allowlist.txt     only paths where sudo() is accepted
verify/config.env.example    disposable database and module test
skills/                      odoo-safe-change, odoo-11-code-review,
                             factorlibre-mr-preflight
evals/cases/                 Odoo code review and FactorLibre preflight
evals/rubric.*.json          weighted rubrics
docs/                        Odoo baseline, environment and plan
tests/test_odoo_lint.py      unit tests for the linter
```

## Use

Copy this directory to the target repo as `.dev-agent/profiles/odoo11` or keep it
under `profiles/odoo11`. The core `guard/guard.sh` reads `.dev-agent/config`
(`DEV_AGENT_PROFILE=odoo11`) and runs `guard/odoo.sh`; it no longer contains Odoo
checks itself. The core `verify/run.sh` runs `E2E_CMD` and keeps the Playwright report and
traces under `evidence/<run-id>/e2e/`; use it for website, portal, SGA or back-office flows.

```bash
cp -a profiles/odoo11 /path/to/repo/.dev-agent/profiles/odoo11
printf 'DEV_AGENT_PROFILE=odoo11\n' > /path/to/repo/.dev-agent/config
```

Fill `verify/config.env` from the example and copy the skill directories into the
agent's skills path or install them with gentle-ai. The eval cases use the core
harness:

```bash
python3 /path/to/dev-agent-kit/evals/harness.py \
  --case-dir evals/cases/odoo-11-code-review/01-seeded \
  --rubric evals/rubric.odoo-11-code-review.json \
  --agent build --model <approved> --judge-model <approved-different> --k 3
```

## rsc-harness and gentle-ai

gentle-ai installs and synchronises agent instructions, skills and MCP; it does
not replace rsc-harness. rsc-harness is the process/spec/ASDD layer. If the repo
uses it, its skills stay in `.rsc/skills` and this profile does not copy them. If
the repo does not use that workflow, this profile works without rsc-harness.

## Company norm

The company norm is `ScalpersCompany/scalpers-tech-doc/AGENTS.md`; the profile
declares `PROFILE_NORM_REPO` and `PROFILE_NORM_PATH` and the core
`scripts/check-techdoc.sh` verifies the clone. The company norm wins; this
profile only adds Odoo rules.

## Agent skills

- SDD is the `spec-driven-development` skill, installed globally in the agent.
- ODD is always-on text in `AGENTS.md`/`SOUL.md`; it is not a skill.
- RDD is the `gentle-ai review` binary; it is not a skill.
- The rsc-harness skills are repo-local in `.rsc/skills`; they are not copied here.

## Boundaries

This profile never deploys, never touches production and never uses the shared
`scalpers` database. The verify example creates a disposable database.
