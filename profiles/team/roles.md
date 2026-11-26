# Team role contract

`roles.json` is the machine-readable contract; this file is the same contract written for a
person. `guard/team_lint.py` reads the JSON and fails the gate when the two drift apart, when
a role loses its exit command, or when a read-only role gains a write surface.

The profile does not replace the language profile. It sits on top of it: `guard/team.sh`
delegates the language checks to the profile named by `TEAM_BASE_PROFILE` in
`.dev-agent/team.env` (for example `odoo11`), so `guard` and `verify` keep one implementation.

## The five roles

| Role | Stage | Writes | Read-only | Runs on a copy | Exit command |
|---|---|---|---|---|---|
| `plan` | specification | `odd/tasks/{task_file}.md` | no | no | `team_lint.py --task odd/tasks/{task_file}.md` |
| `dev` | implementation | `addons/{module}/**` | no | no | `dev-agent guard --staged` and `bash verify/run.sh` |
| `review` | review | nothing | yes | yes | `dev-agent review-gga {tree}` reaching `STATUS: PASSED` |
| `verify` | verification | nothing | yes | yes | `team_lint.py --evidence evidence/{run_id}` |
| `judge` | evaluation | nothing | yes | yes | `team_lint.py --score {score_file}` |

Exactly one role declares `owns_worktree` and exactly one writes source: `dev`. The planner
writes the task file, nobody else writes documents. A reviewer that edits the tree under
review has broken its contract even if the review is correct.

## plan

Writes only the task file. The task file is the specification every other role reads, and the
only handoff format the contract accepts: a role receives a path, a task ID and a list of
`S#`, never a paraphrase of the request.

Exit: `team_lint.py --task` requires `## Specs` with at least one `S<n>`, a `## Tasks` section
where every task row (a `T<n>` bullet or table row) cites an existing `S#` or carries `—` for
scaffolding, and a `## Log` whose first entry is `L1` (the user's original request, verbatim).
A task file that fails this check is not a spec.

Reads: `docs/FEATURE_MAP.md`, `docs/agent-quality/ENVIRONMENT.md`.

## dev

Writes only under the module it implements. It owns the worktree; no other role writes to it
and no second dev works in the same tree. It runs the gate for its own diagnosis, and its
`verify/run.sh` run is progress, not the receipt: the receipt is the verifier's run on a copy.

Exit: `dev-agent guard --staged` passes, and `bash verify/run.sh` exits 0 on its worktree.

Forbidden: `git push`, production URLs, the shared database, a second writer in the tree.

## review

Reads the diff, the task file and the verification summary; writes nothing; works on a copy of
the tree. It appends findings as `path:line` plus the rule broken, and ends with
`STATUS: PASSED` or `STATUS: FAILED`.

Exit: GGA reaches `STATUS: PASSED`. Any finding under a BLOCKING heading is `FAILED`; there is
no "pass with notes". A missing provider or a review that could not run is `ENV-FAIL`, never
`PASSED`.

## verify

Runs the core `verify/run.sh` on a copy and certifies the evidence directory. It never fixes
what it finds: a failing suite goes back to `dev` with the log path.

Exit: `team_lint.py --evidence` accepts `evidence/<run-id>/summary.json`: `status` is `pass`,
`tests` is `pass`, `sha` and `run_id` are non-empty, `e2e` is `pass` when configured, and at
least one check actually ran. A summary that exists but says `fail` is a failed card.

## judge

The kit's eval judge, unchanged: K runs in disposable copies, a judge model different from the
executor, threshold from the rubric (8.5 by default). The role exists here to make the
separation explicit: the judge never scores its own run and never edits the case.

Exit: `team_lint.py --score` accepts `score.json`: `k >= 3`, `passed` true, `mean >= threshold`,
and `judge_model` different from `model`.

## Handoff between roles

Every handoff references the task file. The card or the comment carries one line:

```text
Spec: odd/tasks/<feature>.md, T2, S3-S4
```

and, when a previous stage produced an artifact, its path: `Evidence: evidence/<run-id>/`,
`Review: <comment id>`, `Score: evals/runs/<run-id>/score.json`. A message that only says
"it works" or "looks fine" is not a handoff and does not move the card.

## The chain as one command

`plan`, `dev`, `review` and `verify` run in that order, and the order is executed by
`bin/team-run.sh` instead of remembered. One invocation takes the repository and the task
file, feeds each role its query with `-Q` and the repository as its working directory, applies
a wall-clock timeout and a turn cap per stage, and then decides with the gate, never with what
the role answered:

```bash
.dev-agent/profiles/team/bin/team-run.sh <repo> --spec odd/tasks/<feature>.md [--from <stage>] [--dry-run] [--stub-cli]
```

| Stage | Gate the runner applies |
|---|---|
| `plan` | the task file exists and `team_lint.py --task` exits 0 |
| `dev` | the repository runner exits 0: `make check`, else `VERIFY_CMD` or `TEST_CMD` of `.dev-agent/verify.env` |
| `review` | `evidence/<run-id>/review.md` carries `STATUS: PASSED` |
| `verify` | `team_lint.py --evidence evidence/<run-id>` accepts `summary.json` |

The first failing stage stops the chain and the runner exits with its own code (`20` plan,
`21` dev, `22` review, `23` verify; `10` is a usage error). Every stage logs to
`evidence/<run-id>/`, and the run ends with a summary naming the stage, the gate and the
evidence, so the reason a chain stopped is a file and a line, not a recollection.

## Read-only is a mechanism, not a promise

`review` and `verify` operate on a copy, and the tree they were given is proved unchanged with
two commands:

```bash
python3 .dev-agent/profiles/team/guard/team_lint.py --tree-snapshot <tree>
python3 .dev-agent/profiles/team/guard/team_lint.py --tree-unchanged <tree> <hash>
```

The snapshot hashes `HEAD` plus `git status --porcelain`, so a stray edit, a new untracked file
or a reset all change it. The card keeps the hash it took before the read-only stage and
requires the same hash after it.

## Runner mapping

The contract is agent-neutral: one agent instance per role, whatever runs it, and the same
`roles.json` renders the definitions for each agent (`dev-agent roles claude|opencode`, and a
Hermes profile per role created from the same file). The practical mapping is one instance per
role, the same model family but a different model for `review` and `judge` than for `dev`, and
one queue per repository whose cards carry the task file path. The queue is the audit trail;
the task file is the specification; the gate commands are the only definition of done. A
free-form chat between agents is not part of this contract, because it leaves no row anyone
can read later.
