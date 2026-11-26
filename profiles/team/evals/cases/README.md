# Eval cases

No case yet, on purpose: an eval case is written from an observed failure of the role contract,
with the rubric criteria taken from what the failure showed. The candidates, once they happen:

- a handoff that drops the `S#` reference and still closes the card;
- a review that edits the tree and reports `PASSED`;
- a verify accepted on a `summary.json` with the suite skipped.

Until then the contract is covered by `tests/test_profile_contract.py` and
`tests/test_team_lint.py`, which are deterministic and run in CI.
