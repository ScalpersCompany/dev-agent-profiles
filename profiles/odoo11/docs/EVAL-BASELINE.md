# Eval baselines

Internal baselines. They record the score and what each run observed; they do not name the
executor or the judge. Both are approved internal models, different from each other.

## Odoo 11 code review

- Case: `evals/cases/odoo-11-code-review/01-seeded`
- Skill: `odoo-11-code-review` 1.2.1
- Runs: 3
- Isolation: `copy`
- Scores: 9.44, 10.0, 10.0
- Mean: 9.81; min 9.44; max 10.0; standard deviation 0.26
- Threshold: 8.5; result: pass
- Cost: 0.698729 USD; tokens: 11,489,208 (executor plus judge, summed across steps)

## What the runs observed

Run 1 missed two of the six `help=` fields (`api_key` and `bpost_passphrase_encoded`)
and made two questionable extra claims: that the computed `total` was editable, and a
duplicate asset warning. It still passed at 9.44.

Runs 2 and 3 found every seeded defect, enumerated every field without `help=`, and
returned 10.0. The remaining variance is model adherence to the skill's report
contract, not a missing rule: the contract in 1.2.1 already requires one line per
field without `help=` and v11-only fixes.

## FactorLibre MR preflight

- Case: `evals/cases/factorlibre-mr-preflight/01-seeded`
- Skill: `factorlibre-mr-preflight` 1.1.0
- Runs: 3
- Isolation: `worktree`
- Scores: 9.50, 9.57, 9.50
- Mean: 9.52; min 9.50; max 9.57; standard deviation 0.03
- Threshold: 8.5; result: pass
- Cost: 0.520649 USD; tokens: 2,731,935 (executor plus judge, summed across steps)
- Deterministic output: 6 ERROR, 15 WARN, 4 INFO; the credential scan finds 2 clear fields.

What it found: the eval caught two real defects in the skill scripts.
`scan_secret_fields.py` read a one-line field and swallowed the next, so
`bpost_passphrase_encoded` never appeared; `preflight_mr.py` treated `model="..."`
as an xmlid and emitted false INFOs for `ir.*` and the module's own models. Both are
fixed in 1.1.0.

The three runs reported the six ERROR, the fifteen WARN, both credential fields and the
manual blockers. The only repeated gap is the migration wording: the rubric asked for a
missing `LIMIT`, while the agent correctly reported an unrestricted `UPDATE` without
`WHERE`; the rubric now says "without WHERE or limit". Run 1 also omitted the
`access_loyalty_card_user` row when citing the ACL; runs 2 and 3 cited it.

```bash
python3 evals/harness.py \
  --case-dir evals/cases/factorlibre-mr-preflight/01-seeded \
  --rubric evals/rubric.factorlibre-mr-preflight.json \
  --agent build \
  --model <approved> \
  --judge-model <approved-different> \
  --k 3
```

## dev-verify

- Case: `evals/cases/dev-verify/01-fix-failing-test`
- Skill: `dev-verify` 1.1.0
- Runs: 3
- Isolation: `worktree`
- Scores: 10.0, 10.0, 10.0
- Mean: 10.0; min 10.0; max 10.0; standard deviation 0.0
- Threshold: 8.5; result: pass
- Cost: 0.208256 USD; tokens: 1,308,633 (executor plus judge, summed across steps)

The agent ran `verify/run.sh` first, reported the failing `AssertionError` and the red
evidence, changed only `calc.py`, reran, and cited the passing `summary.json`. The report
used `CHANGED / RAN / EVIDENCE / PENDING`. Run 1 also noticed that the sandbox had the case
files untracked; the task wording now says that is expected, so the PENDING line is not a
false alarm in future runs.

```bash
python3 evals/harness.py \
  --case-dir evals/cases/dev-verify/01-fix-failing-test \
  --rubric evals/rubric.dev-verify.json \
  --agent build \
  --model <approved> \
  --judge-model <approved-different> \
  --k 3
```

## repro-first

- Case: `evals/cases/repro-first/01-discount-bug`
- Skill: `repro-first` 1.1.0
- Runs: 3
- Isolation: `worktree`
- Scores: 10.0, 10.0, 10.0
- Mean: 10.0; min 10.0; max 10.0; standard deviation 0.0
- Threshold: 8.5; result: pass
- Cost: 0.284229 USD; tokens: 1,985,352 (executor plus judge, summed across steps)

The agent wrote `test_shop.py`, reported the failing assertion and exit code, fixed
`shop.py`, reran the test and cited the passing `verify/run.sh` evidence. The first K=3
before the harness change scored 9.31: run 2 lost `no_false` because the diff included
pre-existing support docs (`docs/OPERATIONS.md`, `docs/agent-quality/ENVIRONMENT.md`) that
the agent had not touched. The harness now excludes the support paths from the diff; the
fixed run is 10.0.

```bash
python3 evals/harness.py \
  --case-dir evals/cases/repro-first/01-discount-bug \
  --rubric evals/rubric.repro-first.json \
  --agent build \
  --model <approved> \
  --judge-model <approved-different> \
  --k 3
```

## review-diff

- Case: `evals/cases/review-diff/01-unsafe-handler`
- Skill: `review-diff` 1.0.0 measured; 1.1.0 clarifies line numbers and the `- ` prefix
- Runs: 3
- Isolation: `worktree`
- Scores: 10.0, 10.0, 8.92
- Mean: 9.64; min 8.92; max 10.0; standard deviation 0.51
- Threshold: 8.5; result: pass
- Cost: 0.226343 USD; tokens: 706,880 (executor plus judge, summed across steps)

The first two runs found the six required issues and followed the exact contract. Run 3
used a diff position (`tests/test_service.py:35`) instead of the new-file line and was
penalized for a leading `- ` even though the skill's example uses it; the rubric and the
skill now state the new-file line rule and allow the optional prefix. The skill version is
1.1.0 for that clarification; the 9.64 baseline was measured before the clarification.

```bash
python3 evals/harness.py \
  --case-dir evals/cases/review-diff/01-unsafe-handler \
  --rubric evals/rubric.review-diff.json \
  --agent build \
  --model <approved> \
  --judge-model <approved-different> \
  --k 3
```

## Coverage

| Skill | Case | Real run |
|---|---|---|
| `odoo-11-code-review` | `evals/cases/odoo-11-code-review/01-seeded` | 9.81/10, K=3 |
| `factorlibre-mr-preflight` | `evals/cases/factorlibre-mr-preflight/01-seeded` | 9.52/10, K=3 |
| `dev-verify` | `evals/cases/dev-verify/01-fix-failing-test` | 10.0/10, K=3 |
| `repro-first` | `evals/cases/repro-first/01-discount-bug` | 10.0/10, K=3 |
| `review-diff` | `evals/cases/review-diff/01-unsafe-handler` | 9.64/10, K=3 |
| `correct`, `odoo-safe-change`, `query-readonly` | none | installed; no real run |
| `odoo-11-standards`, `odoo-11-orm-performance`, `odoo-11-credential-security`, `odoo-11-reservas-marketplace`, `sga-e2e-testing`, `gitlab`, `jira-cloud`, `rsc-harness-brain`, `gentle-ai-toolchain`, `odoo-development` | none | installed; no real run |

Only the five listed above have a real score. The rest are installed globally, but they are not
claimed as verified; a case is the next step for each one that matters.

## Odoo 11 command

```bash
python3 evals/harness.py \
  --case-dir evals/cases/odoo-11-code-review/01-seeded \
  --rubric evals/rubric.odoo-11-code-review.json \
  --agent build \
  --model <approved> \
  --judge-model <approved-different> \
  --k 3
```

The shipped rubrics use `REPLACE_WITH_APPROVED_MODEL` placeholders. Do not put the
model names in this document, in a ticket, or in a commit message.
