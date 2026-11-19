#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${GUARD_ROOT:-$(cd "$HERE/../../.." && pwd)}"
ARGS=(--root "$ROOT" --allowlist "$HERE/odoo_allowlist.txt")

if [ "${1:-}" = "--staged" ]; then
  mapfile -d '' FILES < <(git -C "$ROOT" diff --cached --name-only -z --diff-filter=ACMR -- '*.py')
  [ ${#FILES[@]} -eq 0 ] && exit 0
  ARGS+=(--files "${FILES[@]}")
fi

exec python3 "$HERE/odoo_lint.py" "${ARGS[@]}"
