#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE="$(cd "$HERE/.." && pwd)"
ROOT="${GUARD_ROOT:-$(pwd)}"

python3 "$HERE/team_lint.py" --profile "$PROFILE" || exit 1

BASE="${TEAM_BASE_PROFILE:-}"
if [ -z "$BASE" ] && [ -f "$ROOT/.dev-agent/team.env" ]; then
  BASE="$(sed -n 's/^TEAM_BASE_PROFILE=//p' "$ROOT/.dev-agent/team.env" | tail -1)"
fi
BASE="${BASE//\"/}"
BASE="${BASE//\'/}"

if [ -z "$BASE" ]; then
  echo "team: no base profile declared, language checks not delegated"
  exit 0
fi

if [ "$BASE" = "team" ]; then
  echo "team: the base profile cannot be team itself" >&2
  exit 1
fi

for candidate in "$ROOT/.dev-agent/profiles/$BASE" "$ROOT/profiles/$BASE"; do
  if [ -d "$candidate/guard" ]; then
    for check in "$candidate"/guard/*.sh; do
      [ -f "$check" ] || continue
      bash "$check" "$@" || exit 1
    done
    echo "team: base profile checks ran: $BASE"
    exit 0
  fi
done

echo "team: base profile not installed: $BASE" >&2
exit 1
