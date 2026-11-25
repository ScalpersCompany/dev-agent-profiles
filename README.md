# Profiles

Environment profiles for `dev-agent-kit`. One directory per environment:

- `profiles/hexagonal`: hexagonal microservices, contract-first and idempotent; domain guard,
  GGA rules, verify example and the `scalpers-hexagonal-microservice` skill.
- `profiles/odoo11`: Odoo 11 guard, GGA rules, verify, skills, evals and docs.
- `profiles/php`: PHP 8 skeleton with its own GGA rules; PHPStan, PHPCS and PHPUnit are the next step.

The core keeps the contract, the gate and the hooks. A profile supplies the language
content; it does not replace `guard`, `verify` or the hooks. Each profile also owns its
`gga/REVIEW-RULES.md`; the core GGA rules are language-agnostic and the active profile's
rules are appended when the review is installed. Odoo rules never leak into PHP, hexagonal
or a future profile.

## Related repositories

| Repository | Role |
|---|---|
| `ScalpersCompany/dev-agent-kit` | core contract, gate, hooks and template |
| `ScalpersCompany/dev-agent-profiles` | this repository: Odoo 11, PHP 8 and hexagonal profiles |
| `ScalpersCompany/scalpers-tech-doc` | company norm and documentation; canonical `AGENTS.md`, linked at `~/.agents/AGENTS.md`; checked by the core `scripts/check-techdoc.sh` |
| Your development repository | product code in Odoo, PHP or any stack; receives the kit and the active profile at its root, not a copy of the norm |

They are separate repositories, not submodules. The Odoo profile declares
`PROFILE_NORM_REPO` and `PROFILE_NORM_PATH`; it never copies the company norm.

New profiles start from the core template: `dev-agent-kit/profiles/_template`, generated
with `scripts/new-profile.sh` and checked with `scripts/validate-profile.py`. The guide is
`dev-agent-kit/docs/CREAR-PERFIL.md`. A profile without `gga/REVIEW-RULES.md` is rejected:
it must state its own rules, not inherit another language's.

## Use

Copy a profile into the target repository as `.dev-agent/profiles/<name>`, write
`.dev-agent/config` with `DEV_AGENT_PROFILE=<name>`, and fill the profile's
`verify/config.env` from its example. The core `guard/guard.sh` then runs the profile's
`guard/*.sh`.

## Odoo 11

`profiles/odoo11` contains the linter, allowlist, GGA rules, Odoo skills, eval cases,
rubrics and Odoo docs. It never touches production and never uses the shared `scalpers`
database.

## Hexagonal microservices

`profiles/hexagonal` packages the architecture rules and the executable guard for any
Scalpers microservice, whatever its domain: pure domain, contract-first API, ports and
adapters, idempotency, `problem+json`, persistence, tests and Docker. The
`scalpers-hexagonal-microservice` skill carries the full architecture, the company
methodology mapping, the checklist and the service tree. The guard rejects framework, HTTP,
SQL, YAML and infrastructure imports inside `domain/` and `print()` in service code. Its
`gga/REVIEW-RULES.md` adds the microservice contract to the core review.

## rsc-harness and gentle-ai

`gentle-ai` installs and synchronises agents, skills and MCP. It does not replace
`rsc-harness`: the ASDD/SDD workflow and its repo-local `.rsc/skills` are a different layer.
If a repo does not use that workflow, the Odoo profile works without rsc-harness.

## Company norm

The Odoo profile declares `PROFILE_NORM_REPO` and `PROFILE_NORM_PATH` for
`scalpers-tech-doc`; run `scripts/check-techdoc.sh` in the core. The company norm wins;
this profile only adds Odoo rules.

## Status

The repository is public at `https://github.com/ScalpersCompany/dev-agent-profiles`; the `dev-agent init` installer and the lock file are designed but not wired.
