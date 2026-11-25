#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${GUARD_ROOT:-$(pwd)}"
ARGS=(--root "$ROOT")

if [ "${1:-}" = "--staged" ]; then
  mapfile -d '' FILES < <(git -C "$ROOT" diff --cached --name-only -z --diff-filter=ACMR -- '*.py')
  [ ${#FILES[@]} -eq 0 ] && exit 0
  ARGS+=(--files "${FILES[@]}")
fi

exec python3 "$HERE/hexagonal_lint.py" "${ARGS[@]}"
