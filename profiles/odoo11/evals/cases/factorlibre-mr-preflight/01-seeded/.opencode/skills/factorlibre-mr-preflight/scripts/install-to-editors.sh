#!/usr/bin/env bash
# Instala esta skill en las carpetas que leen Claude Code, OpenCode, Codex,
# pi/gentle-shell y la base compartida ~/.agents. Es idempotente: solo toca el
# directorio de esta skill en cada destino.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="factorlibre-mr-preflight"

DESTINATIONS=(
  "$HOME/.agents/skills/software-development/$NAME"
  "$HOME/.claude/skills/$NAME"
  "$HOME/.config/opencode/skills/software-development/$NAME"
  "$HOME/.codex/skills/software-development/$NAME"
  "$HOME/.gentle-shell/agent/skills/software-development/$NAME"
)

# pi tiene su home efectivo en ~/.gentle-shell/agent; si existe el otro home, se cubre tambien.
if [ -d "$HOME/.pi/agent" ]; then
  DESTINATIONS+=("$HOME/.pi/agent/skills/software-development/$NAME")
fi

for dst in "${DESTINATIONS[@]}"; do
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ]; then
    rm -f "$dst"
  fi
  rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' "$SKILL_DIR/" "$dst/"
  echo "instalada: $dst"
done

echo "--- verificacion (sha256 de SKILL.md) ---"
for dst in "${DESTINATIONS[@]}"; do
  printf '%s  %s\n' "$(sha256sum "$dst/SKILL.md" | cut -d' ' -f1)" "$dst"
done
