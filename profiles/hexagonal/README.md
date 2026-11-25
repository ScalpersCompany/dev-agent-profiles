# Hexagonal microservice profile

Profile for Scalpers microservices built with the hexagonal architecture. It packages the
architecture rules, the domain guard, a verify example and the
`scalpers-hexagonal-microservice` skill so any repository can follow the same mechanics.

The base is domain-agnostic: it does not contain product-specific rules.
The same profile serves billing, catalog, notifications, operations or any other service.

## Contents

```text
profile.json                 contract
profile.env                  runtime values
AGENTS.fragment.md           microservice rules added to the repo AGENTS.md
gga/REVIEW-RULES.md          microservice blocking rules appended to the core GGA rules
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

- No framework, HTTP, SQL, YAML or infrastructure import inside any `domain/` directory,
  whatever the service layout.
- No `print()` in service code.
- `--staged` mode checks the index content of the staged Python files; with no staged Python it exits 0 because there is nothing to review. A repository with Python to check but no `domain/` fails explicitly. `--files` requires `--staged`.
- The guard is static: it flags literal dynamic imports and `open()`, but cannot see `getattr(builtins, "__import__")(...)` or a module name built at runtime. Use Python >= 3.11 so `stdlib_module_names` classifies the full standard library.

## Boundaries

- The profile does not deploy, does not touch production and does not use a shared database.
- The profile is independent of the calling system. Integrations with a monolith, ERP or legacy
  system are adapters or separate modules; they are not part of this repository or its compose.
- The pilot keeps one repo with services in subfolders; the repository split from the
  methodology applies when the service moves to platform.
- The company norm wins; this profile only adds microservice rules.
