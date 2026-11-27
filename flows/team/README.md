# Team flow

Flow for work split across several agents on the same repository. It fixes who writes
what, what closes each stage, and how one stage hands off to the next, so that several agents
(one per role, any runner) produce the same auditable result as one careful developer.

It is not a language profile. It adds the role flow and delegates the language checks to
the active profile (or the one declared in `.dev-agent/team.env`), so `guard` and `verify`
keep one implementation.

## Contents

```text
flow.json                    flow contract, declares the entrypoint
flow.schema.json             schema of flow.json
roles.json                   machine-readable role contract
roles.schema.json            schema of roles.json
roles.md                     the same contract for a person
AGENTS.fragment.md           multi-agent rules added to the repo AGENTS.md
gga/REVIEW-RULES.md          blocking rules appended to the core GGA rules
guard/team_lint.py           contract, task file, evidence, score and tree checks
bin/team-run.sh              the four stages in fixed order, stopping at the first red
bin/stub-cli.sh              fake CLI for the runner tests and for a dry rehearsal
verify/config.env.example    verify that inherits the base profile commands
skills/                      no domain skill yet; roles are the mechanism
evals/cases/                 no case yet; a role earns one from an observed failure
tests/                       unit tests for the contract, the checks and the runner
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

Install the language profile first, then run the flow from the repository:

```bash
dev-agent flow list
dev-agent flow run team --spec odd/tasks/<feature>.md --dry-run
```

`dev-agent flow` finds `flows/team` in `dev-agent-profiles`; it does not activate a profile.
If the repo needs an explicit base, write `TEAM_BASE_PROFILE=odoo11` in `.dev-agent/team.env`.

The flow runner validates the role contract and each stage; the active profile supplies guard
and verify. `verify/run.sh` reads `.dev-agent/verify.env`; the flow example sources the base
profile config instead of duplicating commands.

Checks, by hand:

```bash
python3 flows/team/guard/team_lint.py
python3 flows/team/guard/team_lint.py --task odd/tasks/<feature>.md
python3 flows/team/guard/team_lint.py --evidence evidence/<run-id>
python3 flows/team/guard/team_lint.py --score evals/runs/<run-id>/score.json
python3 flows/team/guard/team_lint.py --tree-snapshot <tree>
python3 flows/team/guard/team_lint.py --tree-unchanged <tree> <hash>
```

The first one is the contract lint and also runs before the others. The last two are how a
card proves that a read-only stage left the tree alone.

## The chain as a command

`roles.json` says who closes each stage; `bin/team-run.sh` runs the four stages in that order
and stops at the first one whose gate fails. The order and the gates are data and code, not a
habit: a stage cannot be skipped by forgetting it, and a stage cannot be reported green by the
agent that ran it.

```bash
dev-agent flow run team --spec odd/tasks/<feature>.md
```

`flow.json` declares the entrypoint, and `team_lint.py` fails the contract when the declared
file is missing or is not executable.

| Stage | The runner calls | The runner checks, not the agent's text |
|---|---|---|
| `plan` | `hermes -p plan chat -q <query> -Q --in <repo> --max-turns N` | the task file exists and `team_lint.py --task` exits 0 |
| `dev` | same, `-p dev` | the repository runner exits 0: `make check` when the Makefile has that target, else `VERIFY_CMD` (or `TEST_CMD`) from `.dev-agent/verify.env` |
| `review` | same, `-p review` | `evidence/<run-id>/review.md` contains `STATUS: PASSED` |
| `verify` | same, `-p verify` | `team_lint.py --evidence evidence/<run-id>` accepts `summary.json` |

Options: `--from <stage>` starts at one stage and marks the earlier ones as skipped,
`--dry-run` prints every command and gate and touches nothing, and `--stub-cli [<cli>]` runs a
fake CLI (default `bin/stub-cli.sh`) so the tests exercise the chain without a model call.

Environment: `TEAM_CLI` (default `hermes`), `TEAM_STAGE_TIMEOUT` (1800 s), `TEAM_MAX_TURNS`
(40), `TEAM_EVIDENCE` (default `evidence`), `TEAM_RUN_ID`, `TEAM_SPEC`.

Exit codes: `0` chain green, `10` usage, `20` plan, `21` dev, `22` review, `23` verify. Each
stage writes its own log and the gate output into `evidence/<run-id>/`, and the last block of
the run is a summary with the stage, its result, the gate and where to look.

Because the gate is a command, a red stage is a red chain whatever the agent answered: an
agent that says "done" with a failing `make check` stops the chain at `dev`, and an agent that
says "done" without `STATUS: PASSED` stops it at `review`.

The run directory lives under `evidence/`, which the repository should keep out of version
control: the read-only proof hashes `HEAD` plus `git status --porcelain`, so an `evidence/`
that git does not ignore would make `review` look like it changed the tree it was given.

## Several agents, one board

The flow is agent-neutral: the contract names roles, not products, and `dev-agent roles
<claude|opencode>` renders one agent definition per role from `roles.json` (a Hermes profile
per role is created from the same file). One instance per role, one board per repository, and
cards whose body carries `Spec: odd/tasks/<feature>.md, T2, S3-S4`. The board is the queue and
the audit trail; the task file is the specification; the exit command is the only definition
of done. `review` and `judge` run on a different model from `dev`, for the same reason the
kit's eval uses a different judge: the executor does not grade itself.

## Design notes

- The contract is executable. Roles, write surfaces and exit commands live in `roles.json`,
  and `guard/team_lint.py` fails the gate when a read-only role gains a write surface, when an
  exit command leaves the kit's command list, or when `roles.md` and `roles.json` drift apart.
  A prose-only contract would be a promise, and the kit's rule is that a promise is not a gate.
- Review and verify are read-only by mechanism: they work on a copy and the tree hash taken
  before the stage must match after it. Trusting the agent to not edit was the alternative and
  it does not survive a long session.
- `team` is a flow, not an activatable profile. It composes the active language profile; one
  active language profile per repository stays true, and the language checks keep one
  implementation.
- The planner closes on a linted task file rather than on prose. The `S#`-to-task link is the
  handoff format the rest of the chain depends on, so it is checked, not requested.

## Boundaries

This flow never pushes, never deploys, never touches production and never uses a shared
database. It does not decide delivery: the human does, after reading the evidence.
