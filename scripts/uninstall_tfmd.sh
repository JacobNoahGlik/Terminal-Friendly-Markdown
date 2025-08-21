#!/usr/bin/env bash
# shellcheck shell=bash
# Uninstall TFMD (pipx install), with optional config cleanup.

# Strict mode (portable-ish)
set -Eeuo pipefail 2>/dev/null || {
  set -Eeuo
  (set -o | grep -q 'pipefail') && set -o pipefail || true
}

PURGE_CONFIG=false
if [[ "${1:-}" == "--purge" ]]; then
  PURGE_CONFIG=true
fi

echo "→ Uninstalling TFMD…"

# Prefer to run as the same user who installed via pipx
if ! command -v pipx >/dev/null 2>&1; then
  echo "⚠️  pipx not found. If TFMD was installed with pipx, install pipx first or remove manually:"
  echo "    rm -f \"\$HOME/.local/bin/tfmd\""
  echo "    rm -rf \"\$HOME/.local/share/pipx/venvs/tfmd\" \"\$HOME/.local/pipx/venvs/tfmd\""
else
  # Ensure pipx apps dir is on PATH (not strictly needed to uninstall, but nice)
  pipx ensurepath >/dev/null 2>&1 || true

  # Uninstall (this removes the venv and any injected packages, incl. textual)
  if pipx list | grep -qE 'package +tfmd '; then
    pipx uninstall tfmd
  else
    echo "ℹ️  TFMD not listed in pipx. Continuing with manual cleanup."
  fi
fi

# Remove any leftover shims / venvs just in case
for p in \
  "$HOME/.local/bin/tfmd" \
  "$HOME/.local/share/pipx/venvs/tfmd" \
  "$HOME/.local/pipx/venvs/tfmd"
do
  if [[ -e "$p" ]]; then
    echo "✂  Removing leftover: $p"
    rm -rf -- "$p"
  fi
done

# Optional: remove the EXACT pager defaults we suggested during setup
if $PURGE_CONFIG; then
  if [[ -f "$HOME/.bashrc" ]]; then
    echo "🧹 Purging pager defaults from ~/.bashrc (exact matches only)…"
    cp "$HOME/.bashrc" "$HOME/.bashrc.bak.tfmd.$(date +%s)" || true
    # Remove the exact lines we recommended adding in setup_tfmd.sh
    sed -i \
      -e '/^export LESS="-RF"$/d' \
      -e "/^export LESS='-RF'$/d" \
      -e '/^export PAGER="less -RF"$/d' \
      -e "/^export PAGER='less -RF'$/d" \
      "$HOME/.bashrc" || true
  fi
fi

echo "✅ Done."
echo "   If your shell still shows an old alias or path, open a new terminal or run:  hash -r"
echo "   To reinstall later:  pipx install . && pipx inject tfmd textual"

