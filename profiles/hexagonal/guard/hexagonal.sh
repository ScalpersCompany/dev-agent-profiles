#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${GUARD_ROOT:-$(pwd)}"

if [ "${1:-}" = "--staged" ]; then
  TMP="$(mktemp)" || exit 1
  if ! git -C "$ROOT" diff --cached --relative --name-only -z --diff-filter=ACMR -- '*.py' > "$TMP"; then
    rm -f "$TMP"
    echo "hexagonal: git diff failed for $ROOT" >&2
    exit 1
  fi
  FILES=()
  while IFS= read -r -d '' file; do FILES+=("$file"); done < "$TMP"
  rm -f "$TMP"
  [ ${#FILES[@]} -eq 0 ] && exit 0
  exec python3 "$HERE/hexagonal_lint.py" --root "$ROOT" --staged --files "${FILES[@]}"
fi

exec python3 "$HERE/hexagonal_lint.py" --root "$ROOT"
