#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir repo
cd repo
git init -q -b master
git config user.name Fixture
git config user.email fixture@example.com
cp -a "$ROOT/fixture/base/." .
git add .
git commit -qm "chore: base"
git checkout -qb feature
cp -a "$ROOT/fixture/feature/." .
git add .
git commit -qm "cambios"
