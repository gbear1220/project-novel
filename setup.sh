#!/usr/bin/env bash
set -euo pipefail

PUSH_BACK=false
ALL_AGENTS=false

for arg in "$@"; do
  case "$arg" in
    --push-back) PUSH_BACK=true ;;
    --all-agents) ALL_AGENTS=true ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: ./setup.sh [--push-back] [--all-agents]" >&2
      exit 1
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS=("korean-humanizer" "narrative-forge" "literature-machine")
HOME_AGENTS_SKILLS="$HOME/.agents/skills"

copy_clean_dir() {
  local src="$1"
  local dst="$2"
  rm -rf "$dst"
  mkdir -p "$dst"
  tar -C "$src" --exclude="__pycache__" --exclude="*.pyc" --exclude="*.pyo" -cf - . | tar -C "$dst" -xf -
}

if [ "$PUSH_BACK" = true ]; then
  echo "[Sync] $HOME_AGENTS_SKILLS -> $REPO_ROOT/skills"
  for name in "${SKILLS[@]}"; do
    src="$HOME_AGENTS_SKILLS/$name"
    dst="$REPO_ROOT/skills/$name"
    [ -d "$src" ] || { echo "Missing local skill: $src" >&2; exit 1; }
    copy_clean_dir "$src" "$dst"
    echo "  Synced <- $name"
  done
  echo "[Done] Repository skills updated from local installation."
  exit 0
fi

echo "[Install] $REPO_ROOT/skills -> $HOME_AGENTS_SKILLS"
mkdir -p "$HOME_AGENTS_SKILLS"
for name in "${SKILLS[@]}"; do
  copy_clean_dir "$REPO_ROOT/skills/$name" "$HOME_AGENTS_SKILLS/$name"
  echo "  Installed -> $HOME_AGENTS_SKILLS/$name"
done

if [ "$ALL_AGENTS" = true ]; then
  for agent_root in ".claude" ".codex"; do
    if [ -d "$HOME/$agent_root" ]; then
      mkdir -p "$HOME/$agent_root/skills"
      for name in "${SKILLS[@]}"; do
        copy_clean_dir "$REPO_ROOT/skills/$name" "$HOME/$agent_root/skills/$name"
      done
      echo "  Also synced -> $HOME/$agent_root/skills"
    fi
  done
fi

PY_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PY_BIN" ]; then
  echo "[Warn] Python 3.10+ not found on PATH."
  exit 0
fi

echo "[Smoke Test] Verifying Python CLI checkers..."
"$PY_BIN" "$HOME_AGENTS_SKILLS/korean-humanizer/scripts/audit_korean.py" --help >/dev/null
"$PY_BIN" "$HOME_AGENTS_SKILLS/literature-machine/scripts/novel_checker.py" --help >/dev/null
echo "[OK] Literature Machine is ready on this machine!"
