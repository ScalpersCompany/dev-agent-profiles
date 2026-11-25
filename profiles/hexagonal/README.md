# Hexagonal microservice profile

Profile for Scalpers microservices built with the hexagonal architecture. It packages the
architecture rules, the domain guard, a verify example and the
`scalpers-hexagonal-microservice` skill so any repository can follow the same mechanics.

## Contents

```text
profile.json                 contract
profile.env                  runtime values
AGENTS.fragment.md           microservice rules added to the repo AGENTS.md
guard/hexagonal.sh           guard entry point
guard/hexagonal_lint.py      domain dependency and print checks
verify/config.env.example    boot, health, smoke, test and timeout
skills/                      scalpers-hexagonal-microservice
evals/cases/                 eval cases (baseline pending)
tests/                       unit tests for the guard
docs/                        profile decisions and architecture pointers
```

## Use

Copy this directory to the target repository as `.dev-agent/profiles/hexagonal` and write
the profile name in `.dev-agent/config`:

```bash
mkdir -p /path/to/repo/.dev-agent/profiles
cp -a profiles/hexagonal /path/to/repo/.dev-agent/profiles/hexagonal
printf 'DEV_AGENT_PROFILE=hexagonal\n' > /path/to/repo/.dev-agent/config
```

Fill `verify/config.env` from the example. The core `guard/guard.sh` runs the profile guard;
the core `verify/run.sh` runs the configured test command.

Copy the skill directory to the agent's skills path or install it with `gentle-ai`. The core
generic skills are not copied here.

## What the guard checks

- No framework, HTTP, SQL, YAML or infrastructure import inside any `domain/` directory, in
  both layouts: `services/*/src/*/domain` and `src/*/domain`.
- No `print()` in domain or application code.
- `--staged` mode checks only the staged Python files.

## Boundaries

- The profile does not deploy, does not touch production and does not use a shared database.
- The Odoo bridge stays in `scalpers-v11`; this profile is for the transport or any other
  microservice, never for the Odoo module.
- The pilot keeps one repo with services in subfolders; the repository split from the
  methodology applies when the service moves to platform.
- The company norm wins; this profile only adds microservice rules.
