# Team profile

Profile for work split across several agents on the same repository. It fixes who writes
what, what closes each stage, and how one stage hands off to the next, so that several agents
(one per role, any runner) produce the same auditable result as one careful developer.

It is not a language profile. It adds the role contract and delegates the language checks to
the profile declared as its base, so `guard` and `verify` keep one implementation.

## Contents

```text
profile.json                 contract
profile.env                  runtime values
profile.schema.json          schema of profile.json
roles.json                   machine-readable role contract
roles.schema.json            schema of roles.json
roles.md                     the same contract for a person
AGENTS.fragment.md           multi-agent rules added to the repo AGENTS.md
gga/REVIEW-RULES.md          blocking rules appended to the core GGA rules
guard/team.sh                guard entry point: contract, then the base profile checks
guard/team_lint.py           contract, task file, evidence, score and tree checks
verify/config.env.example    verify that inherits the base profile commands
skills/                      no domain skill yet; roles are the mechanism
evals/cases/                 no case yet; a role earns one from an observed failure
tests/                       unit tests for the contract and the checks
```

## Roles

| Role | Writes | Closing command |
|---|---|---|
| `plan` | `odd/tasks/<feature>.md` | `team_lint.py --task odd/tasks/<feature>.md` |
| `dev` | `addons/<module>/**` | `dev-agent guard --staged`, `bash verify/run.sh` |
| `review` | nothing, on a copy | `dev-agent review-gga <tree>` → `STATUS: PASSED` |
| `verify` | nothing, on a copy | `team_lint.py --evidence evidence/<run-id>` |
| `judge` | nothing, on a copy | `team_lint.py --score <score.json>` |

`roles.md` carries the detail; `roles.json` is what the gate reads.

## Use

Install the language profile first and the team profile next to it, then declare the base:

```bash
cp -a profiles/odoo11 /path/to/repo/.dev-agent/profiles/odoo11
cp -a profiles/team   /path/to/repo/.dev-agent/profiles/team
printf 'DEV_AGENT_PROFILE=team\n' > /path/to/repo/.dev-agent/config
printf 'TEAM_BASE_PROFILE=odoo11\n' > /path/to/repo/.dev-agent/team.env
```

`guard/guard.sh` then runs `guard/team.sh`, which validates the role contract and executes the
base profile's guard scripts. `verify/run.sh` reads `.dev-agent/verify.env`; the team example
sources the base profile's config instead of duplicating its commands.

Checks, by hand:

```bash
python3 .dev-agent/profiles/team/guard/team_lint.py
python3 .dev-agent/profiles/team/guard/team_lint.py --task odd/tasks/<feature>.md
python3 .dev-agent/profiles/team/guard/team_lint.py --evidence evidence/<run-id>
python3 .dev-agent/profiles/team/guard/team_lint.py --score evals/runs/<run-id>/score.json
python3 .dev-agent/profiles/team/guard/team_lint.py --tree-snapshot <tree>
python3 .dev-agent/profiles/team/guard/team_lint.py --tree-unchanged <tree> <hash>
```

The first one is the contract lint and also runs before the others. The last two are how a
card proves that a read-only stage left the tree alone.

## Several agents, one board

The profile is agent-neutral: the contract names roles, not products. With Hermes the mapping
is one profile per role, one board per repository, and cards whose body carries
`Spec: odd/tasks/<feature>.md, T2, S3-S4`. The board is the queue and the audit trail; the task
file is the specification; the exit command is the only definition of done. `review` and
`judge` run on a different model from `dev`, for the same reason the kit's eval uses a
different judge: the executor does not grade itself.

## Design notes

- The contract is executable. Roles, write surfaces and exit commands live in `roles.json`,
  and `guard/team_lint.py` fails the gate when a read-only role gains a write surface, when an
  exit command leaves the kit's command list, or when `roles.md` and `roles.json` drift apart.
  A prose-only contract would be a promise, and the kit's rule is that a promise is not a gate.
- Review and verify are read-only by mechanism: they work on a copy and the tree hash taken
  before the stage must match after it. Trusting the agent to not edit was the alternative and
  it does not survive a long session.
- `team` is an activatable profile that delegates to a base one, instead of a second
  coordination layer beside the language profile. One active profile per repository stays true,
  and the language checks keep one implementation.
- The planner closes on a linted task file rather than on prose. The `S#`-to-task link is the
  handoff format the rest of the chain depends on, so it is checked, not requested.

## Boundaries

This profile never pushes, never deploys, never touches production and never uses a shared
database. It does not decide delivery: the human does, after reading the evidence.
