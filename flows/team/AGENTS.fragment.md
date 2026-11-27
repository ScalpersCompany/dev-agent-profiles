# Team flow rules

- The company norm is `ScalpersCompany/scalpers-tech-doc/AGENTS.md`; this fragment only adds the multi-agent rules. If they conflict, the company norm wins.
- The flow runs over one active language profile, or over `TEAM_BASE_PROFILE` in `.dev-agent/team.env`; the flow adds the role gate and never reimplements the language checks.
- One role per agent. `plan` writes the task file, `dev` writes source, `review`, `verify` and `judge` write nothing and work on a copy.
- Every handoff cites `odd/tasks/<feature>.md`, the task ID and the `S#` list; a paraphrase is not a handoff.
- A card is done only with the exit command of its role: `dev-agent guard --staged`, `bash verify/run.sh` with `evidence/<run-id>/summary.json` at `pass`, `dev-agent review-gga` at `STATUS: PASSED`, or an accepted `score.json`.
- Review and verify keep the tree they were given unchanged; the card records the tree hash before and after.
- No role pushes, deploys or touches production; the shared database is never a test target.
- The four stages run through the flow entrypoint (`dev-agent flow run team --spec <task-file>`); a stage advances on its gate command, never on a role saying it is done.
- The judge is a different model from the executor and never scores its own run.
- A role that cannot run its gate reports `ENV-FAIL`; it never reports `PASSED`.
