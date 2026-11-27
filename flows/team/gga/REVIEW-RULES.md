# GGA rules — team flow

These rules are appended to the DevAgentKit core GGA rules. They add the contract for work
split across several agents on one repository: who may write, what proves a stage, and how one
stage hands off to the next. The company rule, the core rules and the base profile rules still
apply.

## BLOCKING — multi-agent coordination

### Handoff

- A stage that starts or ends without a reference to `odd/tasks/<feature>.md`, the task ID and
  the `S#` it covers. A paraphrase of the request, a chat summary or "same as before" is
  `FAILED`.
- A stage whose card and task file disagree about the scope: a task list that cites an `S#`
  the file does not have, or a spec rewritten inside the card without a new `## Log` entry and
  a reopened task.
- A delivery without the four-line block from the core rules (`CHANGED`, `RAN`, `EVIDENCE`,
  `PENDING`). A claim without command output is `FAILED`.

### Write surfaces

- A write outside the role's declared surface: the planner outside `odd/tasks/`, the
  implementer outside its module, any write at all from `review`, `verify` or `judge`.
- Two implementers on the same tree or the same module in one card chain. Serialise or use
  separate copies; a merge of two unverified changes is not a work unit.
- A reviewer or verifier that edits, formats, reverts or resets the tree it was given. The tree
  hash before and after the stage must match; a difference is `FAILED` even when the result is
  better.

### Evidence and gates

- `review` reaching `PASSED` with a blocking finding, with a provider missing, or without the
  command output. An unavailable reviewer is `ENV-FAIL`, never `PASSED`.
- `verify` accepted on a `summary.json` whose `status`, `tests` or configured `e2e` is not
  `pass`, or whose `sha` and `run_id` are empty. A suite that did not run is not a pass.
- `judge` accepted with `k < 3`, with `judge_model` equal to `model`, or with
  `mean < threshold`. The executor never scores itself.
- A gate bypassed with `--no-verify`, a lowered threshold, a skipped test or a deleted rule to
  close the card.

### Boundaries

- Any `git push`, merge request creation, deploy or production access by any role. Delivery is
  a human decision recorded outside the card.
- A production URL, a production credential or the shared database in any command the profile
  runs; tests use a disposable database.
- A secret in code, in a card body or in a log the card keeps.

## ADVISORY — team

- A card body that restates the task file instead of citing it.
- A task file with specs no task covers and no note saying they are pending.
- A role that runs a command outside its declared exit list, even when the result is useful.
- A board with cards but no owner or no next action.
