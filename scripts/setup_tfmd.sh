#!/usr/bin/env bash
# shellcheck shell=bash
# TFMD setup for WSL/Linux

# Strict mode (portable-ish)
set -Eeuo pipefail 2>/dev/null || {
  set -Eeuo
  (set -o | grep -q 'pipefail') && set -o pipefail || true
}

# --- sanity: run as a normal user (not root) ---
if [ "${EUID:-$(id -u)}" -eq 0 ]; then
  echo "Please run as a regular user (not root)."
  echo "Open WSL as your user and re-run: ./scripts/setup_tfmd.sh"
  exit 1
fi

# --- require repo root (pyproject + tfmd/ present) ---
if [ ! -f "pyproject.toml" ] || [ ! -d "tfmd" ]; then
  echo "Run this from the repo root (where pyproject.toml lives)."
  exit 1
fi

# --- ensure pipx ---
if ! command -v pipx >/dev/null 2>&1; then
  if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y pipx
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y pipx
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm pipx
  else
    echo "Couldn't auto-install pipx (unknown package manager). Install pipx, then rerun."
    exit 1
  fi
fi

# --- PATH for pipx apps ---
pipx ensurepath >/dev/null 2>&1 || true
case ":$PATH:" in
  *":$HOME/.local/bin:"*) : ;;
  *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

# --- locale + pager defaults (nice UX) ---
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export LESS='-RF'
export PAGER='less -RF'

# --- install TFMD (into pipx venv) ---
pipx install . --force

# --- add Textual for TUI (mouse wheel, etc.) ---
pipx inject tfmd textual

# --- optional: verify ---
pipx runpip tfmd show textual >/dev/null 2>&1 || true

echo
echo "✅ TFMD installed."
echo "Try: tfmd README.md --toc --soft-wrap --backend tui"
echo "     (or: tfmd README.md --backend less)"
echo
echo "If 'tfmd' isn’t found, start a new shell or run:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
