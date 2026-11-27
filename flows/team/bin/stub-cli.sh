#!/usr/bin/env bash
set -uo pipefail

role=""
previous=""
for argument in "$@"; do
  [ "$previous" = "-p" ] && role="$argument"
  previous="$argument"
done

if [ -z "$role" ]; then
  echo "stub-cli: no -p <role> in the command line" >&2
  exit 2
fi

printf 'stub-cli: role=%s repo=%s run=%s\n' "$role" "${TEAM_REPO:-}" "${TEAM_RUN_ID:-}"
printf 'stub-cli: spec=%s\n' "${TEAM_SPEC:-}"

if [ "${STUB_FAIL_ROLE:-}" = "$role" ]; then
  echo "stub-cli: simulated failure in $role" >&2
  exit 1
fi

case "$role" in
  review)
    mkdir -p "$(dirname "$TEAM_VERDICT")"
    status="${STUB_REVIEW_STATUS:-PASSED}"
    {
      printf '# Review of %s\n\n' "${TEAM_SPEC:-}"
      printf 'stub verdict, no model was called\n\n'
      printf 'STATUS: %s\n' "$status"
    } >"$TEAM_VERDICT"
    printf 'stub-cli: wrote %s\n' "$TEAM_VERDICT"
    ;;
  verify)
    mkdir -p "$TEAM_RUN_DIR"
    sha="$(git -C "${TEAM_REPO:-.}" rev-parse --verify HEAD 2>/dev/null | head -1)"
    [ -n "$sha" ] || sha="no-sha"
    {
      printf '{\n'
      printf '  "run_id": "%s",\n' "${TEAM_RUN_ID:-stub}"
      printf '  "sha": "%s",\n' "$sha"
      printf '  "status": "%s",\n' "${STUB_VERIFY_STATUS:-pass}"
      printf '  "smoke": "skipped",\n'
      printf '  "tests": "%s",\n' "${STUB_VERIFY_TESTS:-pass}"
      printf '  "e2e": "%s"\n' "${STUB_VERIFY_E2E:-skipped}"
      printf '}\n'
    } >"$TEAM_RUN_DIR/summary.json"
    printf 'stub-cli: wrote %s\n' "$TEAM_RUN_DIR/summary.json"
    ;;
esac

exit 0
