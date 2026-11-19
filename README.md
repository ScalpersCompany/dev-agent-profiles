# Profiles

Private environment profiles for `dev-agent-kit`. One directory per environment:

- `profiles/odoo11`: Odoo 11 guard, verify, skills, evals and docs.
- `profiles/php`: PHP skeleton; PHPStan, PHPCS and PHPUnit are the next step.

The core keeps the contract, the gate and the hooks. A profile supplies the language
content; it does not replace `guard`, `verify` or the hooks.

## Use

Copy a profile into the target repository as `.dev-agent/profiles/<name>`, write
`.dev-agent/config` with `DEV_AGENT_PROFILE=<name>`, and fill the profile's
`verify/config.env` from its example. The core `guard/guard.sh` then runs the profile's
`guard/*.sh`.

## Odoo 11

`profiles/odoo11` contains the linter, allowlist, Odoo skills, eval cases, rubrics and
Odoo docs. It never touches production and never uses the shared `scalpers` database.

## rsc-harness and gentle-ai

`gentle-ai` installs and synchronises agents, skills and MCP. It does not replace
`rsc-harness`: the ASDD/SDD workflow and its repo-local `.rsc/skills` are a different layer.
If a repo does not use that workflow, the Odoo profile works without rsc-harness.

## Status

The repository is local; the private remote is pending. The `dev-agent init` installer and
the lock file are designed but not wired.
