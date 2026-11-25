# Profile eval cases

The eval baseline is pending. Add one case per new skill rule with `TASK.md`,
`context.json`, the fixture and a rubric in `evals/rubric.<name>.json`.

The harness is the core one (`dev-agent-kit/evals/harness.py`). Run K=3 with a judge
different from the executor and threshold 8.5. A case without a rubric or without
`context.json` is not a real eval. Record the result in `docs/EVAL-BASELINE.md`.
