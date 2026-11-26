#!/usr/bin/env bash
set -uo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

STAGES="plan dev review verify"
EXIT_USAGE=10
EXIT_PLAN=20
EXIT_DEV=21
EXIT_REVIEW=22
EXIT_VERIFY=23

usage() {
  cat <<'USAGE'
usage: team-run.sh <repo> --spec <task-file> [--from <stage>] [--dry-run] [--stub-cli [<cli>]]

Runs plan, dev, review and verify in that order and stops at the first stage
whose gate fails.

  <repo>            repository the chain works on
  --spec <file>     task file the chain reads and checks (relative to <repo>)
  --from <stage>    start at plan, dev, review or verify; earlier stages are skipped
  --dry-run         print every command and gate, run nothing, create nothing
  --stub-cli [cli]  run a fake CLI instead of the model (default: bin/stub-cli.sh)

Environment:
  TEAM_CLI            CLI binary (default: hermes)
  TEAM_PYTHON         python used for the profile checks (default: python3)
  TEAM_STAGE_TIMEOUT  seconds per stage (default: 1800)
  TEAM_MAX_TURNS      turn cap per stage (default: 40)
  TEAM_EVIDENCE       evidence directory, relative to <repo> (default: evidence)
  TEAM_RUN_ID         run identifier (default: current UTC timestamp)
  TEAM_SPEC           task file, when --spec is not given

Exit codes: 0 chain green, 10 usage, 20 plan, 21 dev, 22 review, 23 verify.
USAGE
}

CLI="${TEAM_CLI:-hermes}"
PYTHON="${TEAM_PYTHON:-python3}"
STAGE_TIMEOUT="${TEAM_STAGE_TIMEOUT:-1800}"
MAX_TURNS="${TEAM_MAX_TURNS:-40}"
EVIDENCE_NAME="${TEAM_EVIDENCE:-evidence}"
RUN_ID="${TEAM_RUN_ID:-}"
STUB=""

repo=""
spec="${TEAM_SPEC:-}"
from=""
dry_run=0

while [ $# -gt 0 ]; do
  case "$1" in
    --spec)
      [ $# -ge 2 ] || { echo "team-run: --spec needs a value" >&2; exit "$EXIT_USAGE"; }
      spec="$2"
      shift 2
      ;;
    --from)
      [ $# -ge 2 ] || { echo "team-run: --from needs a value" >&2; exit "$EXIT_USAGE"; }
      from="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --stub-cli)
      if [ $# -ge 2 ] && [ "${2#-}" = "$2" ]; then
        STUB="$2"
        shift 2
      else
        STUB="$PROFILE_DIR/bin/stub-cli.sh"
        shift
      fi
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "team-run: unknown option: $1" >&2
      usage >&2
      exit "$EXIT_USAGE"
      ;;
    *)
      if [ -n "$repo" ]; then
        echo "team-run: unexpected argument: $1" >&2
        exit "$EXIT_USAGE"
      fi
      repo="$1"
      shift
      ;;
  esac
done

if [ -z "$repo" ] || [ -z "$spec" ]; then
  echo "team-run: a repository and --spec are required" >&2
  usage >&2
  exit "$EXIT_USAGE"
fi

if [ ! -d "$repo" ]; then
  echo "team-run: not a directory: $repo" >&2
  exit "$EXIT_USAGE"
fi
repo="$(cd "$repo" && pwd)"

case "$spec" in
  /*) spec_abs="$spec"; spec_rel="$spec" ;;
  *)  spec_abs="$repo/$spec"; spec_rel="$spec" ;;
esac

if [ -n "$from" ]; then
  case " $STAGES " in
    *" $from "*) ;;
    *) echo "team-run: unknown stage for --from: $from" >&2; exit "$EXIT_USAGE" ;;
  esac
fi

if [ -n "$STUB" ] && [ ! -x "$STUB" ]; then
  echo "team-run: stub CLI is not executable: $STUB" >&2
  exit "$EXIT_USAGE"
fi
if [ -z "$STUB" ] && ! command -v "$CLI" >/dev/null 2>&1; then
  echo "team-run: CLI not found: $CLI" >&2
  exit "$EXIT_USAGE"
fi
[ -n "$STUB" ] && CLI="$STUB"

RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

case "$EVIDENCE_NAME" in
  /*) evidence_dir="$EVIDENCE_NAME" ;;
  *)  evidence_dir="$repo/$EVIDENCE_NAME" ;;
esac
run_dir="$evidence_dir/$RUN_ID"
verdict="$run_dir/review.md"

lint="$repo/.dev-agent/profiles/team/guard/team_lint.py"
[ -f "$lint" ] || lint="$PROFILE_DIR/guard/team_lint.py"

stage_query() {
  case "$1" in
    plan)
      printf 'Plan spec %s. Write the task file with Specs (S#), Tasks (T# citing S#) and Log (L1, the request verbatim). Do not change source code, and run the plan exit command before you answer.' "$spec_rel"
      ;;
    dev)
      printf 'Implement spec %s, one task at a time, with its tests and its documentation in the same change. Run the repository checks before you answer.' "$spec_rel"
      ;;
    review)
      printf 'Review spec %s against the tree at %s. Read only: do not edit the tree. Write the verdict to %s and end it with STATUS: PASSED or STATUS: FAILED.' "$spec_rel" "$repo" "$verdict"
      ;;
    verify)
      printf 'Verify the change in %s. Write the evidence for run %s into %s: summary.json with run_id, sha, status, tests and e2e. Do not edit the tree under test.' "$repo" "$RUN_ID" "$run_dir"
      ;;
  esac
}

stage_gate() {
  case "$1" in
    plan) printf 'task file %s exists and team_lint --task exits 0' "$spec_rel" ;;
    dev) printf 'the repository runner exits 0 (make check, else VERIFY_CMD of .dev-agent/verify.env)' ;;
    review) printf 'a verdict file contains STATUS: PASSED (%s)' "$verdict" ;;
    verify) printf 'summary.json of the run passes team_lint --evidence (%s)' "$run_dir" ;;
  esac
}

gate_plan() {
  if [ ! -f "$spec_abs" ]; then
    printf 'missing task file: %s\n' "$spec_rel"
    return 1
  fi
  if [ ! -f "$lint" ]; then
    printf 'missing profile check: %s\n' "$lint"
    return 1
  fi
  if ! "$PYTHON" "$lint" --task "$spec_abs" >"$run_dir/plan.team_lint.log" 2>&1; then
    printf 'team_lint --task rejected %s\n' "$spec_rel"
    sed 's/^/  /' "$run_dir/plan.team_lint.log"
    return 1
  fi
  printf 'team_lint accepted %s\n' "$spec_rel"
}

gate_dev() {
  local runner="" value=""
  if [ -f "$repo/Makefile" ] && grep -qE '^check[[:space:]]*:' "$repo/Makefile"; then
    runner="make check"
  elif [ -f "$repo/.dev-agent/verify.env" ]; then
    value="$( cd "$repo" && set +u; . ./.dev-agent/verify.env >/dev/null 2>&1; printf '%s' "${VERIFY_CMD:-${TEST_CMD:-}}" )"
    runner="$value"
  fi
  if [ -z "$runner" ]; then
    printf 'no repository runner: no check target in Makefile and no VERIFY_CMD or TEST_CMD in .dev-agent/verify.env\n'
    return 1
  fi
  printf 'runner: %s\n' "$runner"
  if ! ( cd "$repo" && TEAM_RUN_DIR="$run_dir" timeout "$STAGE_TIMEOUT" bash -c "$runner" ) >"$run_dir/dev.runner.log" 2>&1; then
    printf 'runner failed: %s\n' "$runner"
    sed 's/^/  /' "$run_dir/dev.runner.log"
    return 1
  fi
  printf 'runner exited 0\n'
}

gate_review() {
  if [ ! -f "$verdict" ]; then
    printf 'missing verdict file: %s\n' "$verdict"
    return 1
  fi
  if ! grep -qE 'STATUS:[[:space:]]*PASSED' "$verdict"; then
    printf 'verdict is not PASSED: %s\n' "$verdict"
    return 1
  fi
  printf 'verdict PASSED: %s\n' "$verdict"
}

gate_verify() {
  if [ ! -f "$lint" ]; then
    printf 'missing profile check: %s\n' "$lint"
    return 1
  fi
  if ! "$PYTHON" "$lint" --evidence "$run_dir" >"$run_dir/verify.team_lint.log" 2>&1; then
    printf 'evidence rejected: %s\n' "$run_dir"
    sed 's/^/  /' "$run_dir/verify.team_lint.log"
    return 1
  fi
  printf 'evidence accepted: %s\n' "$run_dir"
}

gate() {
  case "$1" in
    plan) gate_plan ;;
    dev) gate_dev ;;
    review) gate_review ;;
    verify) gate_verify ;;
  esac
}

stage_exit() {
  case "$1" in
    plan) printf '%s' "$EXIT_PLAN" ;;
    dev) printf '%s' "$EXIT_DEV" ;;
    review) printf '%s' "$EXIT_REVIEW" ;;
    verify) printf '%s' "$EXIT_VERIFY" ;;
  esac
}

run_stage=0
for stage in $STAGES; do
  if [ -n "$from" ] && [ "$run_stage" = 0 ]; then
    [ "$stage" = "$from" ] && run_stage=1
  fi
done

if [ "$dry_run" = 1 ]; then
  printf 'team-run: dry run, nothing is executed\n'
  printf 'repo: %s\nspec: %s\nrun:  %s\n\n' "$repo" "$spec_rel" "$run_dir"
  skipping=1
  [ -z "$from" ] && skipping=0
  for stage in $STAGES; do
    if [ "$skipping" = 1 ] && [ "$stage" != "$from" ]; then
      printf '%-8s skip   gate: %s\n' "$stage" "$(stage_gate "$stage")"
      continue
    fi
    skipping=0
    printf '%-8s run    %s -p %s chat -q <query> -Q --in %s --max-turns %s\n' \
      "$stage" "$CLI" "$stage" "$repo" "$MAX_TURNS"
    printf '%-8s        query: %s\n' "" "$(stage_query "$stage")"
    printf '%-8s        timeout: %ss\n' "" "$STAGE_TIMEOUT"
    printf '%-8s        gate: %s\n' "" "$(stage_gate "$stage")"
  done
  printf '\nteam-run: dry run, no stage executed and nothing written\n'
  exit 0
fi

mkdir -p "$run_dir"

printf 'team-run: repo %s\n' "$repo"
printf 'team-run: spec %s\n' "$spec_rel"
printf 'team-run: run  %s\n\n' "$run_dir"

results=""
failed_stage=""

skipping=1
[ -z "$from" ] && skipping=0
for stage in $STAGES; do
  if [ "$skipping" = 1 ] && [ "$stage" != "$from" ]; then
    results="$results$stage|skipped|skipped by --from|-
"
    continue
  fi
  skipping=0

  query="$(stage_query "$stage")"
  printf '== %s\n' "$stage"
  printf '   cli  %s -p %s chat -q -Q --in %s --max-turns %s\n' "$CLI" "$stage" "$repo" "$MAX_TURNS"

  (
    cd "$repo" || exit 1
    TEAM_ROLE="$stage" \
    TEAM_REPO="$repo" \
    TEAM_SPEC="$spec_rel" \
    TEAM_RUN_ID="$RUN_ID" \
    TEAM_RUN_DIR="$run_dir" \
    TEAM_VERDICT="$verdict" \
    TEAM_EVIDENCE_DIR="$evidence_dir" \
      timeout "$STAGE_TIMEOUT" "$CLI" -p "$stage" chat -q "$query" -Q --in "$repo" --max-turns "$MAX_TURNS"
  ) >"$run_dir/$stage.log" 2>&1
  rc=$?

  if [ "$rc" -ne 0 ]; then
    if [ "$rc" -eq 124 ]; then
      reason="timed out after ${STAGE_TIMEOUT}s"
    else
      reason="the CLI exited $rc"
    fi
    printf '   fail: %s\n' "$reason"
    sed 's/^/   | /' "$run_dir/$stage.log"
    results="$results$stage|fail|$reason|$run_dir/$stage.log
"
    failed_stage="$stage"
    break
  fi

  gate_out="$(gate "$stage" 2>&1)"
  gate_rc=$?
  printf '%s\n' "$gate_out" | sed 's/^/   | /'
  if [ "$gate_rc" -ne 0 ]; then
    results="$results$stage|fail|gate: $(printf '%s' "$gate_out" | head -1)|$run_dir/$stage.log
"
    failed_stage="$stage"
    break
  fi
  printf '   pass\n'
  results="$results$stage|pass|$(printf '%s' "$gate_out" | head -1)|$run_dir/$stage.log
"
done

printf '\nteam-run: summary\n'
printf '  %-8s %-8s %s\n' stage result gate
printf '%s' "$results" | while IFS='|' read -r stage result gate evidence; do
  [ -n "$stage" ] || continue
  printf '  %-8s %-8s %s\n' "$stage" "$result" "$gate"
done

if [ -n "$failed_stage" ]; then
  printf '\nteam-run: stopped at %s (exit %s)\n' "$failed_stage" "$(stage_exit "$failed_stage")"
  exit "$(stage_exit "$failed_stage")"
fi

printf '\nteam-run: chain green, evidence in %s\n' "$run_dir"
exit 0
